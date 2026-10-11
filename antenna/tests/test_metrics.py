import numpy as np
from analysis import metrics

def _notch(f0=2.45e9, depth=0.01, q=20):
    f = np.linspace(2e9, 3e9, 201)
    s = 1 - (1 - depth) / (1 + 1j * q * (f / f0 - f0 / f))
    return f, s

def test_s11_min_finds_notch_between_grid_points():
    f, s = _notch(f0=2.4537e9)
    fm, dbm = metrics.s11_min(f, s)
    assert abs(fm - 2.4537e9) < 1e6 and dbm < -30

def test_band_edges_bracket_the_minimum():
    f, s = _notch()
    lo, hi = metrics.band_edges(f, s, -10)
    assert lo < 2.45e9 < hi

def test_band_edges_none_when_no_crossing():
    f = np.linspace(2e9, 3e9, 11); s = np.full(11, 0.5 + 0j)   # -6 dB everywhere
    assert metrics.band_edges(f, s, -10) is None

def test_db_at_interpolates():
    f, s = _notch()
    assert metrics.db_at(f, s, 2.45e9) < -30
