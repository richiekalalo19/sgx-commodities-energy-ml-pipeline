"""Validation harness (plan task 7). Design fixed on 2026-11-10; inputs are refreshed once after the
Bloomberg pull, then the lockbox is sealed for good.

D2  Universe: a core counter is eligible on a sample date if its median daily traded value (unadjusted
    close x volume, S$) over the trailing 252 SGX sessions is at least S$100,000.
D3  Targets: forward residual returns (sum of the daily residuals from scripts/15) over 5 and 20 sessions.
    The long-only base rebalances monthly on the 20-session target; a later long-short variant may use either.
    Rank IC, tercile spread (top third minus bottom third, the long-short test) and hit rate at both horizons.
Samples: the 20-session target on the last SGX session of each month, the 5-session target on the last
    session of each week.
Folds: expanding walk-forward. Test periods are calendar years 2018 to 2024, then 1 Jan to 30 Apr 2025.
    Purge: a training sample's target window must end before its test period starts.
    Embargo: a further EMBARGO sessions between the end of the last training window and the test start.
Lockbox: samples dated on or after LOCKBOX_START, stored apart and opened once with `open_lockbox`.
    Samples whose target window crosses into the lockbox are dropped from both sides.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime

import numpy as np
import pandas as pd

from . import config

LOCKBOX_START = pd.Timestamp("2025-05-01")
MIN_VALUE_SGD = 100_000
VALUE_WINDOW = 252
HORIZONS = (5, 20)
EMBARGO = 20
TEST_PERIODS = [(f"{y}", pd.Timestamp(f"{y}-01-01"), pd.Timestamp(f"{y}-12-31")) for y in range(2018, 2025)] + [
    ("2025a", pd.Timestamp("2025-01-01"), LOCKBOX_START - pd.Timedelta(days=1))]
DIR = config.PROCESSED / "harness"
OPENED = DIR / "lockbox_opened.json"


# ---------------------------------------------------------------- construction
def eligibility(close: pd.DataFrame, volume: pd.DataFrame, sessions: pd.DatetimeIndex) -> pd.DataFrame:
    """Sessions x counters, True when the trailing median traded value clears the D2 threshold."""
    value = close * volume                          # full history, so 2014 samples have a trailing year
    median = value.rolling(VALUE_WINDOW, min_periods=VALUE_WINDOW // 2).median()
    return (median >= MIN_VALUE_SGD).reindex(sessions, method="ffill")


def sample_dates(sessions: pd.DatetimeIndex, h: int) -> pd.DatetimeIndex:
    s = pd.Series(sessions, index=sessions)
    key = s.dt.to_period("M") if h == 20 else s.dt.to_period("W-FRI")
    return pd.DatetimeIndex(s.groupby(key).max().values)


def forward_sum(resid: pd.DataFrame, h: int) -> pd.DataFrame:
    """Sum of residuals over sessions t+1 .. t+h; needs at least 80% of those sessions."""
    rev = resid.iloc[::-1].rolling(h, min_periods=int(np.ceil(0.8 * h))).sum().iloc[::-1]
    return rev.shift(-1)


def build_samples(resid: pd.DataFrame, elig: pd.DataFrame) -> pd.DataFrame:
    sessions = resid.index
    lb = sessions.searchsorted(LOCKBOX_START)
    pos = pd.Series(np.arange(len(sessions)), index=sessions)
    out = []
    for h in HORIZONS:
        y = forward_sum(resid, h)
        for t in sample_dates(sessions, h):
            i = int(pos[t])
            if i + h >= len(sessions):
                continue                                   # target window runs past the data
            part = "dev" if i + h < lb else ("lockbox" if i >= lb else None)
            if part is None:
                continue                                   # window crosses into the lockbox
            yt, et = y.loc[t], elig.loc[t]
            for code in resid.columns:
                if pd.notna(yt[code]):
                    out.append((t, code, h, float(yt[code]), bool(et.get(code, False)), part))
    df = pd.DataFrame(out, columns=["date", "code", "horizon", "target", "eligible", "part"])
    df["fold"] = "train-only"
    for name, a, b in TEST_PERIODS:
        df.loc[(df["part"] == "dev") & df["date"].between(a, b), "fold"] = name
    df.loc[df["part"] == "lockbox", "fold"] = "lockbox"
    return df


def folds(sessions: pd.DatetimeIndex, h: int) -> list[dict]:
    """For each test period, the last sample date allowed in training (purge + embargo)."""
    out = []
    for name, a, b in TEST_PERIODS:
        start = sessions.searchsorted(a)
        last_train_pos = start - h - EMBARGO - 1          # its window ends EMBARGO sessions before the test
        out.append(dict(fold=name, horizon=h, test_start=str(sessions[start].date()),
                        test_end=str(min(b, sessions[-1]).date()), train_last=str(sessions[last_train_pos].date())))
    return out


def save(samples: pd.DataFrame, fold_table: list[dict]) -> dict:
    if OPENED.exists():
        raise RuntimeError(f"The lockbox was opened ({OPENED.read_text().strip()}); the harness cannot be rebuilt.")
    DIR.mkdir(parents=True, exist_ok=True)
    samples[samples["part"] == "dev"].to_parquet(DIR / "dev.parquet", index=False)
    lock = samples[samples["part"] == "lockbox"]
    lock.to_parquet(DIR / "lockbox_sealed.parquet", index=False)
    seal = dict(created=datetime.now().isoformat(timespec="seconds"), rows=len(lock),
                lockbox_start=str(LOCKBOX_START.date()),
                sha256=hashlib.sha256((DIR / "lockbox_sealed.parquet").read_bytes()).hexdigest())
    (DIR / "seal.json").write_text(json.dumps(seal, indent=1))
    (DIR / "folds.json").write_text(json.dumps(fold_table, indent=1))
    return seal


# ---------------------------------------------------------------- use
def load_dev(h: int | None = None) -> pd.DataFrame:
    df = pd.read_parquet(DIR / "dev.parquet")
    return df if h is None else df[df["horizon"] == h]


def train_test(dev: pd.DataFrame, h: int, fold: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    f = next(x for x in json.loads((DIR / "folds.json").read_text()) if x["fold"] == fold and x["horizon"] == h)
    d = dev[dev["horizon"] == h]
    train = d[d["date"] <= pd.Timestamp(f["train_last"])]
    test = d[d["fold"] == fold]
    return train, test


def open_lockbox(confirm: str) -> pd.DataFrame:
    """Opens the lockbox exactly once, after the final specification is frozen."""
    if confirm != "open once":
        raise ValueError('Pass confirm="open once" to open the lockbox.')
    if OPENED.exists():
        raise RuntimeError(f"Already opened: {OPENED.read_text().strip()}")
    seal = json.loads((DIR / "seal.json").read_text())
    digest = hashlib.sha256((DIR / "lockbox_sealed.parquet").read_bytes()).hexdigest()
    if digest != seal["sha256"]:
        raise RuntimeError("Lockbox file does not match its seal.")
    OPENED.write_text(json.dumps(dict(opened=datetime.now().isoformat(timespec="seconds"))))
    return pd.read_parquet(DIR / "lockbox_sealed.parquet")


# ---------------------------------------------------------------- evaluation (plan: IC, tercile spread, hit rate)
def per_date_scores(df: pd.DataFrame, pred: str = "pred", min_names: int = 6) -> pd.DataFrame:
    rows = []
    for (h, d), g in df[df["eligible"]].dropna(subset=[pred, "target"]).groupby(["horizon", "date"]):
        if len(g) < min_names:
            continue
        ic = g[pred].rank().corr(g["target"].rank())
        third = pd.qcut(g[pred].rank(method="first"), 3, labels=False)
        spread = g.loc[third == 2, "target"].mean() - g.loc[third == 0, "target"].mean()
        hit = float((np.sign(g[pred]) == np.sign(g["target"])).mean())
        auc_up = rank_auc(g[pred], g["target"] > 0)
        top = pd.qcut(g["target"].rank(method="first"), 3, labels=False) == 2
        auc_top = rank_auc(g[pred], top)
        rows.append((h, d, len(g), ic, spread, hit, auc_up, auc_top))
    return pd.DataFrame(rows, columns=["horizon", "date", "n", "ic", "tercile_spread", "hit_rate",
                                       "auc_up", "auc_top"])


def rank_auc(score: pd.Series, label: pd.Series) -> float:
    """ROC-AUC via the Mann-Whitney statistic (ties count half); NaN if only one class is present.

    auc_up uses label = residual > 0; auc_top uses label = realised top tercile, the names a long-only
    portfolio would want to hold. 0.5 is no skill.
    """
    label = np.asarray(label, bool)
    n1, n0 = int(label.sum()), int((~label).sum())
    if n1 == 0 or n0 == 0:
        return np.nan
    r = pd.Series(np.asarray(score, float)).rank().to_numpy()
    return float((r[label].sum() - n1 * (n1 + 1) / 2) / (n1 * n0))


def stationary_bootstrap(x, mean_block: float = 6, n_boot: int = 2000, seed: int = 0) -> tuple[float, float, float]:
    """Mean with a 95% stationary-bootstrap interval (Politis and Romano), for serially dependent scores."""
    x = np.asarray(x, float)
    x = x[np.isfinite(x)]
    n, rng, p = len(x), np.random.default_rng(seed), 1 / mean_block
    stats = np.empty(n_boot)
    for b in range(n_boot):
        idx = np.empty(n, int)
        idx[0] = rng.integers(n)
        jump = rng.random(n) < p
        fresh = rng.integers(n, size=n)
        for i in range(1, n):
            idx[i] = fresh[i] if jump[i] else (idx[i - 1] + 1) % n
        stats[b] = x[idx].mean()
    return float(x.mean()), float(np.quantile(stats, 0.025)), float(np.quantile(stats, 0.975))
