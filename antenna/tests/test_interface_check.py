"""Field continuity across a plane x = const between two media (air | liver). No COMSOL here: fields are synthetic."""
import numpy as np
import pytest
from analysis.interface_check import eps_complex, continuity

EPS0 = 8.8541878128e-12

def test_eps_complex_of_liver_at_2p4_ghz():
    e = eps_complex(43.2, 1.69, 2.4e9)
    assert e.real == pytest.approx(43.2)
    assert e.imag == pytest.approx(-1.69 / (2 * np.pi * 2.4e9 * EPS0), rel=1e-9)   # about -12.66

def test_physical_fields_pass_both_conditions():
    ec = eps_complex(43.2, 1.69, 2.4e9)
    air = np.array([[900 + 300j, 40 - 10j, 25 + 5j]])            # Ex (normal), Ey, Ez on the air side
    liv = np.array([[(900 + 300j) / ec, 40 - 10j, 25 + 5j]])      # normal D continuous, tangential E continuous
    r = continuity(air, liv, eps_a=1.0, eps_b=ec)
    assert r["tangential_mismatch"][0] < 1e-12
    assert r["normal_D_mismatch"][0] < 1e-12
    assert r["normal_share_a"][0] == pytest.approx(abs(900 + 300j) ** 2 / np.sum(np.abs(air) ** 2))
    assert r["norm_ratio"][0] == pytest.approx(np.linalg.norm(air) / np.linalg.norm(liv))

def test_tangential_jump_is_flagged():
    air = np.array([[1.0, 100.0, 0.0]]); liv = np.array([[1.0 / 45, 10.0, 0.0]])
    r = continuity(air, liv, eps_a=1.0, eps_b=45.0)
    assert r["tangential_mismatch"][0] == pytest.approx(0.9)
    assert r["normal_D_mismatch"][0] < 1e-12

def test_same_medium_control_expects_no_jump_in_any_component():
    a = np.array([[3 + 1j, 2.0, 1.0], [0.5, 0.1j, 7.0]])
    r = continuity(a, a.copy(), eps_a=2.1, eps_b=2.1)
    assert np.all(r["tangential_mismatch"] < 1e-12) and np.all(r["normal_D_mismatch"] < 1e-12)
    assert np.allclose(r["norm_ratio"], 1.0)
