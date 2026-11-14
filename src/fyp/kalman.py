"""Time-varying regression coefficients by Kalman filter, with maximum-likelihood noise variances.

Observation:  y_t = x_t' b_t + e_t,      e_t ~ N(0, r)
State:        b_t = b_{t-1} + w_t,       w_t ~ N(0, diag(q))

Coefficients with q = 0 stay constant (recursive least squares); the rest drift as random walks.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.optimize import minimize


@dataclass
class KalmanResult:
    filtered: np.ndarray      # (T, k) b_t | data up to t
    smoothed: np.ndarray      # (T, k) b_t | all data
    filtered_var: np.ndarray  # (T, k) diagonal of the filtered covariance
    r: float
    q: np.ndarray
    loglik: float


def _filter(y, X, q, r, b0, P0):
    T, k = X.shape
    b, P = b0.copy(), P0.copy()
    Q = np.diag(q)
    filt = np.zeros((T, k)); Pf = np.zeros((T, k, k))
    bpred = np.zeros((T, k)); Ppred = np.zeros((T, k, k))
    ll = 0.0
    for t in range(T):
        bp, Pp = b, P + Q
        bpred[t], Ppred[t] = bp, Pp
        x = X[t]
        if np.isfinite(y[t]) and np.all(np.isfinite(x)):
            v = y[t] - x @ bp
            Px = Pp @ x
            F = x @ Px + r
            K = Px / F
            b = bp + K * v
            P = Pp - np.outer(K, Px)
            ll += -0.5 * (np.log(2 * np.pi * F) + v * v / F)
        else:
            b, P = bp, Pp
        filt[t], Pf[t] = b, P
    return filt, Pf, bpred, Ppred, ll


def _smooth(filt, Pf, bpred, Ppred):
    T, k = filt.shape
    bs, Ps = filt.copy(), Pf.copy()
    for t in range(T - 2, -1, -1):
        C = Pf[t] @ np.linalg.pinv(Ppred[t + 1])
        bs[t] = filt[t] + C @ (bs[t + 1] - bpred[t + 1])
        Ps[t] = Pf[t] + C @ (Ps[t + 1] - Ppred[t + 1]) @ C.T
    return bs, Ps


@dataclass
class FixedRun:
    filtered: np.ndarray      # (T, k) b_t | data up to t
    smoothed: np.ndarray      # (T, k) b_t | all data
    b0: np.ndarray            # starting coefficients (least squares on the first `burn` observations)


def filter_fixed(y: np.ndarray, X: np.ndarray, q: np.ndarray, r: float, burn: int = 60) -> FixedRun:
    """Runs the filter and smoother with noise variances fixed in advance, for example estimated by
    `fit` on an earlier part of the sample. Starting values are set exactly as in `fit`."""
    y = np.asarray(y, float); X = np.asarray(X, float)
    ok = np.isfinite(y) & np.all(np.isfinite(X), axis=1)
    first = np.flatnonzero(ok)[:burn]
    b0 = np.linalg.lstsq(X[first], y[first], rcond=None)[0]
    P0 = np.eye(X.shape[1]) * 1.0
    filt, Pf, bpred, Ppred, _ = _filter(y, X, np.asarray(q, float), float(r), b0, P0)
    sm, _ = _smooth(filt, Pf, bpred, Ppred)
    return FixedRun(filtered=filt, smoothed=sm, b0=b0)


def fit(y: np.ndarray, X: np.ndarray, varying: list[int], burn: int = 60) -> KalmanResult:
    """Estimates r and the q of the `varying` coefficients by maximum likelihood.

    The first `burn` observations set the starting coefficients by least squares and are
    left out of the likelihood.
    """
    y = np.asarray(y, float); X = np.asarray(X, float)
    ok = np.isfinite(y) & np.all(np.isfinite(X), axis=1)
    first = np.flatnonzero(ok)[:burn]
    b0 = np.linalg.lstsq(X[first], y[first], rcond=None)[0]
    resid_var = float(np.var(y[first] - X[first] @ b0)) or 1e-4
    k = X.shape[1]
    P0 = np.eye(k) * 1.0

    def unpack(theta):
        r = np.exp(theta[0])
        q = np.zeros(k)
        q[varying] = np.exp(theta[1:])
        return r, q

    def negll(theta):
        r, q = unpack(theta)
        *_, ll_all = _filter(y[burn:], X[burn:], q, r, b0, P0)
        return -ll_all

    theta0 = np.r_[np.log(resid_var), np.full(len(varying), np.log(resid_var * 1e-3))]
    bounds = [(np.log(resid_var) - 6, np.log(resid_var) + 3)] + [(np.log(resid_var) - 16, np.log(resid_var))] * len(varying)
    opt = minimize(negll, theta0, method="L-BFGS-B", bounds=bounds)
    r, q = unpack(opt.x)
    filt, Pf, bpred, Ppred, ll = _filter(y, X, q, r, b0, P0)
    sm, _ = _smooth(filt, Pf, bpred, Ppred)
    var = np.array([np.diag(p) for p in Pf])
    return KalmanResult(filtered=filt, smoothed=sm, filtered_var=var, r=r, q=q, loglik=-opt.fun)
