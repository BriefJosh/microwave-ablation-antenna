"""Field continuity across a plane x = const between medium a (x below the face) and medium b (x above it).
Maxwell at a source-free face: tangential E (Ey, Ez) continuous; normal D continuous, i.e. eps_a Ex_a = eps_b Ex_b with complex eps = eps_r - j sigma/(omega eps0).
Fields as rows (Ex, Ey, Ez), complex, one row per point pair."""
import numpy as np

EPS0 = 8.8541878128e-12

def eps_complex(eps_r, sigma, f_hz):
    return complex(eps_r, -sigma / (2 * np.pi * f_hz * EPS0))

def continuity(Ea, Eb, eps_a, eps_b):
    Ea, Eb = np.atleast_2d(np.asarray(Ea, complex)), np.atleast_2d(np.asarray(Eb, complex))
    ta, tb = Ea[:, 1:], Eb[:, 1:]
    na = np.linalg.norm(Ea, axis=1)
    return {
        "tangential_mismatch": np.linalg.norm(ta - tb, axis=1) / np.maximum(np.linalg.norm(ta, axis=1), 1e-300),
        "normal_D_mismatch": np.abs(eps_a * Ea[:, 0] - eps_b * Eb[:, 0]) / np.maximum(np.abs(eps_a * Ea[:, 0]), 1e-300),
        "normal_share_a": np.abs(Ea[:, 0]) ** 2 / np.maximum(na ** 2, 1e-300),   # fraction of |E|^2 on side a carried by the normal component
        "norm_ratio": na / np.maximum(np.linalg.norm(Eb, axis=1), 1e-300),          # |E|_a / |E|_b: the step the slice plot shows
    }
