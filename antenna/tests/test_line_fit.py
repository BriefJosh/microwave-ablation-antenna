"""Transmission-line fit: recover Z0, gamma and the load impedance from V(x), I(x) sampled along a uniform line."""
import numpy as np
import pytest
from analysis.line_fit import fit_line, zin_transform

def synth(z0, gamma, zl, length, n, noise=0.0, seed=0):
    """V and I along a line of length `length` ending in load zl, x measured from the source end; V_end = 1."""
    x = np.linspace(0.0, length, n)
    rho = (zl - z0) / (zl + z0)
    # I(x) = (A e^{+g(L-x)} - B e^{-g(L-x)}) / Z0 with A = 1/(1+rho), B = rho/(1+rho)
    a, b = 1 / (1 + rho), rho / (1 + rho)
    v = a * np.exp(gamma * (length - x)) + b * np.exp(-gamma * (length - x))
    i = (a * np.exp(gamma * (length - x)) - b * np.exp(-gamma * (length - x))) / z0
    if noise:
        r = np.random.default_rng(seed)
        v = v * (1 + noise * (r.standard_normal(n) + 1j * r.standard_normal(n)))
        i = i * (1 + noise * (r.standard_normal(n) + 1j * r.standard_normal(n)))
    return x, v, i

def test_recovers_z0_gamma_and_load_without_noise():
    z0, g, zl = 31.5, 0.002 + 1j * 0.62, 12.7 + 4.5j        # gamma in 1/mm: beta 0.62 rad/mm is a wavelength of about 10 mm
    x, v, i = synth(z0, g, zl, 54.0, 55)
    r = fit_line(x, v, i)
    assert abs(r["z0"] - z0) < 1e-6
    assert abs(r["gamma"] - g) < 1e-9
    assert abs(r["z_end"] - zl) < 1e-6

def test_tolerates_one_percent_noise():
    z0, g, zl = 31.5, 0.002 + 1j * 0.62, 12.7 + 4.5j
    x, v, i = synth(z0, g, zl, 54.0, 109, noise=0.01)
    r = fit_line(x, v, i)
    assert abs(r["z0"] - z0) / z0 < 0.05
    assert abs(r["gamma"].imag - g.imag) / g.imag < 0.02

def test_zin_transform_matches_the_synthetic_line():
    z0, g, zl = 31.5, 0.002 + 1j * 0.62, 12.7 + 4.5j
    x, v, i = synth(z0, g, zl, 54.0, 55)
    assert abs(zin_transform(zl, z0, g, 54.0) - v[0] / i[0]) < 1e-6

def test_rejects_non_uniform_grid():
    x = np.array([0.0, 1.0, 3.0, 4.0]); v = np.ones(4, complex); i = np.ones(4, complex)
    with pytest.raises(ValueError):
        fit_line(x, v, i)
