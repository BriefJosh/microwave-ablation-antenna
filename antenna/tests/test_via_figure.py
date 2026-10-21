"""summarize() turns one S11 sweep into the record's table columns."""
import numpy as np
import pytest
from analysis.via_figure import summarize

F = np.arange(2.30e9, 2.6001e9, 0.025e9)

def test_synthetic_dip():
    s = 1 - 0.95 / (1 + 1j * (F - 2.46e9) / 0.04e9)
    r = summarize(F, s)
    assert abs(r["dip_ghz"] - 2.46) < 0.005
    assert r["band_lo_ghz"] < 2.45 < r["band_hi_ghz"]
    assert r["margin_lo_mhz"] == pytest.approx((2.45 - r["band_lo_ghz"]) * 1000, abs=0.05)
    assert r["margin_hi_mhz"] == pytest.approx((r["band_hi_ghz"] - 2.45) * 1000, abs=0.05)
    assert r["width_mhz"] == pytest.approx((r["band_hi_ghz"] - r["band_lo_ghz"]) * 1000, abs=0.05)
    assert r["s11_245_db"] < -10

def test_matched_point_gives_50_ohm():
    assert summarize(F, np.zeros_like(F, dtype=complex) + 1e-9)["zin_245"] == pytest.approx(50, abs=1e-3)

def test_no_band_when_never_below_minus_10():
    r = summarize(F, np.full(F.shape, 0.5 + 0j))
    assert r["band_lo_ghz"] is None and r["margin_lo_mhz"] is None
