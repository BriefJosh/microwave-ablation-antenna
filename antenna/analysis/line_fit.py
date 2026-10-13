"""Transmission-line fit of V(x), I(x) sampled on a uniform grid along a uniform line (x increases away from the source).
V(x) = A e^{-g x} + B e^{+g x} and Z0 I(x) = A e^{-g x} - B e^{+g x}. On a grid of step h, V(x-h) + V(x+h) = 2 cosh(g h) V(x) holds for V and for I,
and V(x+h) - V(x-h) = -2 sinh(g h) Z0 I(x). Least squares over the interior points gives g and Z0; the load impedance is V/I at the last point.
Units: x in mm gives g in 1/mm. Nothing here knows about COMSOL."""
import numpy as np

def _uniform(x):
    d = np.diff(x)
    if len(x) < 5 or not np.allclose(d, d[0], rtol=1e-6):
        raise ValueError("need at least 5 points on a uniform grid")
    return float(d[0])

def fit_line(x, v, i):
    x = np.asarray(x, float); v = np.asarray(v, complex); i = np.asarray(i, complex)
    h = _uniform(x)
    s = np.sqrt(np.sum(abs(v) ** 2) / np.sum(abs(i) ** 2))          # scale I so V and I carry equal weight
    j = i * s
    num = np.sum(np.conj(v[1:-1]) * (v[:-2] + v[2:])) + np.sum(np.conj(j[1:-1]) * (j[:-2] + j[2:]))
    c = num / (2 * (np.sum(abs(v[1:-1]) ** 2) + np.sum(abs(j[1:-1]) ** 2)))
    g = np.arccosh(c) / h
    g = complex(abs(g.real), abs(g.imag))                            # forward wave e^{-g x}: loss Re g >= 0, phase lag Im g > 0
    sh = np.sinh(g * h)
    z0 = np.sum(np.conj(i[1:-1]) * -(v[2:] - v[:-2])) / (2 * sh * np.sum(abs(i[1:-1]) ** 2))
    return {"z0": complex(z0), "gamma": complex(g), "z_end": complex(v[-1] / i[-1]), "z_start": complex(v[0] / i[0]), "h": h}

def zin_transform(zl, z0, gamma, length):
    t = np.tanh(gamma * length)
    return z0 * (zl + z0 * t) / (z0 + zl * t)
