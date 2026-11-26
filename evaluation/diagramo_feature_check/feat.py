"""Kinematic features from SVC pen signals, mirroring Model A's feature ideas.

SVC row: x y t(ms) pen_status azimuth altitude pressure (columns may vary; we use x,y,t,status).
"""
import numpy as np


def load_svc(path):
    rows = []
    with open(path, encoding="utf-8", errors="ignore") as f:
        lines = f.read().strip().splitlines()
    for l in lines[1:]:
        p = l.split()
        if len(p) >= 4:
            try:
                rows.append([float(v) for v in p[:7]] + [np.nan] * (7 - len(p[:7])))
            except ValueError:
                pass
    if len(rows) < 50:
        return None
    a = np.array(rows, dtype=float)
    return a


def resample(t, x, y, s, hz):
    tt = np.arange(t[0], t[-1], 1.0 / hz)
    return tt, np.interp(tt, t, x), np.interp(tt, t, y), (np.interp(tt, t, s) > 0.5).astype(float)


def features(a, hz=None):
    t = a[:, 2] - a[:, 2][0]
    if np.median(np.diff(t)) > 1:
        t = t / 1000.0
    x, y, s = a[:, 0], a[:, 1], (a[:, 3] > 0).astype(float)
    keep = np.r_[True, np.diff(t) > 0]
    t, x, y, s = t[keep], x[keep], y[keep], s[keep]
    if hz is None:
        hz = 1.0 / np.median(np.diff(t))
        tt = np.arange(t[0], t[-1], 1.0 / hz)
        x, y, s = np.interp(tt, t, x), np.interp(tt, t, y), (np.interp(tt, t, s) > 0.5).astype(float)
        t = tt
    else:
        t, x, y, s = resample(t, x, y, s, hz)
    dt = 1.0 / hz
    dur = t[-1] - t[0]
    vx, vy = np.gradient(x, dt), np.gradient(y, dt)
    v = np.hypot(vx, vy)
    on = s > 0
    out = {}
    out["duration_s"] = dur
    out["on_surface_frac"] = on.mean()
    lifts = np.sum((s[1:] == 0) & (s[:-1] == 1))
    out["pen_lifts_per_s"] = lifts / max(dur, 1e-6)
    von = v[on]
    if von.size < 20:
        return None
    thr = 0.05 * np.percentile(von, 95)
    out["pause_frac_on_surface"] = np.mean(von < thr)
    out["mean_speed_on"] = von.mean()
    out["speed_cv_on"] = von.std() / (von.mean() + 1e-9)
    ax, ay = np.gradient(vx, dt), np.gradient(vy, dt)
    jx, jy = np.gradient(ax, dt), np.gradient(ay, dt)
    j2 = (jx ** 2 + jy ** 2)[on]
    path = np.sum(v[on]) * dt
    T = on.sum() * dt
    out["norm_jerk"] = np.log(np.sqrt(0.5 * np.sum(j2) * dt * T ** 5 / (path ** 2 + 1e-9)) + 1e-9)
    # tremor: share of velocity power in 4-12 Hz, on-surface segments concatenated
    sig = von - von.mean()
    if sig.size > 64:
        P = np.abs(np.fft.rfft(sig * np.hanning(sig.size))) ** 2
        f = np.fft.rfftfreq(sig.size, dt)
        band = (f >= 4) & (f <= 12)
        tot = (f >= 0.5) & (f <= min(hz / 2, 25))
        out["tremor_4_12_ratio"] = P[band].sum() / (P[tot].sum() + 1e-12)
        out["dominant_freq"] = f[tot][np.argmax(P[tot])]
    else:
        out["tremor_4_12_ratio"] = np.nan
        out["dominant_freq"] = np.nan
    return out
