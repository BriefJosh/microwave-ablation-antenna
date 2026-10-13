"""Sampling plan and integrators for V(x) and I(x) on the SICL cross-section (y-z plane at fixed x). No COMSOL here: fields are synthetic."""
import numpy as np
import pytest
from analysis.field_sampling import plan, integrate

Z_IN, Z_TOP = 0.465, 0.665          # mm, Wen stack: inner strip and top plate

def wire_h(pts, i0, y0=0.0, z0=Z_IN):
    """H of a straight wire along +x through (y0, z0), counterclockwise in the (y, z) plane."""
    y, z = pts[:, 1] - y0, pts[:, 2] - z0
    r2 = y * y + z * z
    return -i0 / (2 * np.pi) * z / r2, i0 / (2 * np.pi) * y / r2

def test_loop_recovers_wire_current():
    pl = plan([10.0], Z_IN, Z_TOP)
    hy, hz = wire_h(pl["points"], 0.37 - 0.12j)     # amperes per mm of length units cancel: H in A/mm, lengths in mm
    out = integrate(pl, np.zeros(len(hy), complex), hy, hz)
    assert abs(out["I"][0] - (0.37 - 0.12j)) < 1e-4 * abs(0.37 - 0.12j)

def test_loop_is_independent_of_wire_offset_inside_the_loop():
    pl = plan([10.0], Z_IN, Z_TOP)
    hy, hz = wire_h(pl["points"], 1.0, y0=0.08, z0=Z_IN + 0.03)
    out = integrate(pl, np.zeros(len(hy), complex), hy, hz)
    assert abs(out["I"][0] - 1.0) < 1e-3

def test_wire_outside_the_loop_gives_zero():
    pl = plan([10.0], Z_IN, Z_TOP)
    hy, hz = wire_h(pl["points"], 1.0, y0=1.0)
    out = integrate(pl, np.zeros(len(hy), complex), hy, hz)
    assert abs(out["I"][0]) < 1e-3

def test_voltage_is_ez_times_gap():
    pl = plan([10.0, 11.0], Z_IN, Z_TOP)
    ez = np.full(len(pl["points"]), 2.0 + 1.0j)      # V/mm everywhere
    out = integrate(pl, ez, np.zeros_like(ez), np.zeros_like(ez))
    assert np.allclose(out["V"], (2.0 + 1.0j) * (Z_TOP - Z_IN), rtol=1e-3)

def test_points_are_in_mm_and_cover_every_x():
    pl = plan([5.0, 6.0, 7.0], Z_IN, Z_TOP)
    xs = np.unique(pl["points"][:, 0])
    assert np.allclose(xs, [5.0, 6.0, 7.0])
    assert pl["points"].shape[1] == 3

def test_loop_must_stay_clear_of_the_plates():
    with pytest.raises(ValueError):
        plan([1.0], Z_IN, Z_IN + 0.11, delta=0.1)       # loop top would be within 0.01 mm of the plate
