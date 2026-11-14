"""Chart style shared by every figure: validated categorical slots, hairline solid grids,
2px lines, 8px+ dots with a surface ring, labels in ink colours, and light and dark
variants of every figure.

Palette: dataviz reference instance, slots 1-3 (validated all-pairs in both modes; light
slot 3 sits below 3:1 contrast, so charts that use it carry direct labels and a table).
Magnitudes on a log scale are drawn as dots, never bars, because bar length on a log axis
depends on an arbitrary baseline.
"""
from __future__ import annotations

from contextlib import contextmanager

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from . import config  # noqa: E402

THEMES = {
    "light": dict(surface="#fcfcfb", ink="#0b0b0b", ink2="#52514e", muted="#898781",
                  grid="#e1e0d9", axis="#c3c2b7", s1="#2a78d6", s2="#eb6834", s3="#1baf7a",
                  s1_soft="#86b6ef", band="#f0efec"),
    "dark": dict(surface="#1a1a19", ink="#f0efec", ink2="#c3c2b7", muted="#898781",
                 grid="#2c2c2a", axis="#383835", s1="#3987e5", s2="#d95926", s3="#199e70",
                 s1_soft="#184f95", band="#2c2c2a"),
}
FONT = ["Helvetica Neue", "Arial", "DejaVu Sans"]
LINE_W = 1.6      # points; about 2px at the exported size
DOT_SIZE = 7.0    # points; well above 8px at the exported size
RING_W = 1.4      # surface-coloured ring around dots


@contextmanager
def figure(mode: str, w: float = 8.0, h: float = 4.5, ncols: int = 1, sharey: bool = False):
    t = THEMES[mode]
    with plt.rc_context({
        "font.family": "sans-serif", "font.sans-serif": FONT, "font.size": 10.5,
        "axes.facecolor": t["surface"], "figure.facecolor": t["surface"],
        "axes.edgecolor": t["axis"], "axes.labelcolor": t["ink2"], "axes.titlecolor": t["ink"],
        "xtick.color": t["muted"], "ytick.color": t["muted"], "xtick.labelcolor": t["ink2"],
        "ytick.labelcolor": t["ink2"], "text.color": t["ink"],
        "axes.grid": True, "grid.color": t["grid"], "grid.linewidth": 0.8, "grid.linestyle": "-",
        "axes.axisbelow": True, "axes.spines.top": False, "axes.spines.right": False,
        "axes.titlesize": 13, "axes.titleweight": "bold", "axes.titlelocation": "left",
        "legend.frameon": False, "legend.fontsize": 9.5, "legend.labelcolor": t["ink2"],
    }):
        fig, ax = plt.subplots(1, ncols, figsize=(w, h), sharey=sharey, squeeze=True)
        yield fig, ax, t


def titles(ax, t, title: str, subtitle: str = ""):
    ax.set_title(title, pad=24 if subtitle else 10)
    if subtitle:
        ax.text(0, 1.025, subtitle, transform=ax.transAxes, fontsize=9.5, color=t["ink2"], va="bottom")


def source(fig, t, text: str):
    fig.text(0.01, -0.02, text, fontsize=8, color=t["muted"], ha="left", va="top")


def dots(ax, x, y, color, t, size: float = DOT_SIZE, zorder: int = 3, **kw):
    return ax.plot(x, y, linestyle="none", marker="o", markersize=size, markerfacecolor=color,
                   markeredgecolor=t["surface"], markeredgewidth=RING_W, zorder=zorder, **kw)


def save(fig, name: str, mode: str):
    config.FIGURES.mkdir(parents=True, exist_ok=True)
    stem = config.FIGURES / f"{name}_{mode}"
    fig.savefig(stem.with_suffix(".png"), dpi=200, bbox_inches="tight", facecolor=fig.get_facecolor())
    fig.savefig(stem.with_suffix(".svg"), bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)
