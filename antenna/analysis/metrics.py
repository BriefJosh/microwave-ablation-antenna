import numpy as np

def db(s): return 20 * np.log10(np.abs(s))

def s11_min(f, s):
    y = db(s); i = int(np.argmin(y))
    if 0 < i < len(f) - 1:
        x0, x1, x2 = f[i - 1:i + 2]; y0, y1, y2 = y[i - 1:i + 2]
        den = (x0 - x1) * (x0 - x2) * (x1 - x2)
        A = (x2 * (y1 - y0) + x1 * (y0 - y2) + x0 * (y2 - y1)) / den
        B = (x2**2 * (y0 - y1) + x1**2 * (y2 - y0) + x0**2 * (y1 - y2)) / den
        if A > 0:
            fm = -B / (2 * A); C = y1 - A * x1**2 - B * x1
            return fm, A * fm**2 + B * fm + C
    return f[i], y[i]

def band_edges(f, s, level_db=-10.0):
    y = db(s) - level_db; i = int(np.argmin(y))
    if y[i] >= 0: return None
    lo = next((k for k in range(i, 0, -1) if y[k - 1] >= 0), None)
    hi = next((k for k in range(i, len(y) - 1) if y[k + 1] >= 0), None)
    if lo is None or hi is None: return None
    f_lo = f[lo - 1] + (f[lo] - f[lo - 1]) * y[lo - 1] / (y[lo - 1] - y[lo])
    f_hi = f[hi] + (f[hi + 1] - f[hi]) * y[hi] / (y[hi] - y[hi + 1])
    return f_lo, f_hi

def db_at(f, s, f0): return float(np.interp(f0, f, db(s)))

def rel(a, b): return abs(a - b) / abs(b)
