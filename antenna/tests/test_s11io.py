import numpy as np
from analysis import s11io

def _ts(tmp_path, fmt, unit="GHZ"):
    f = np.array([2.0, 2.5, 3.0]); s = np.array([0.5 + 0.1j, 0.05 - 0.02j, 0.3 + 0.4j])
    scale = {"GHZ": 1, "MHZ": 1e3, "HZ": 1e9}[unit]
    rows = []
    for fi, si in zip(f, s):
        if fmt == "RI": a, b = si.real, si.imag
        elif fmt == "MA": a, b = abs(si), np.degrees(np.angle(si))
        else: a, b = 20 * np.log10(abs(si)), np.degrees(np.angle(si))
        rows.append(f"{fi*scale:.9g} {a:.12g} {b:.12g}")
    p = tmp_path / f"t_{fmt}_{unit}.s1p"
    p.write_text(f"! test\n# {unit} S {fmt} R 50\n" + "\n".join(rows) + "\n")
    return p, f * 1e9, s

def test_touchstone_formats_agree(tmp_path):
    for fmt in ("RI", "MA", "DB"):
        for unit in ("GHZ", "MHZ", "HZ"):
            p, f, s = _ts(tmp_path, fmt, unit)
            ff, ss = s11io.read_touchstone(p)
            assert np.allclose(ff, f) and np.allclose(ss, s, atol=1e-9)

def test_palace_csv_matches_touchstone(tmp_path):
    f = np.array([2.0, 2.5]); s = np.array([0.5 + 0.1j, 0.05 - 0.02j])
    p = tmp_path / "port-S.csv"
    p.write_text("f (GHz), |S[1][1]| (dB), arg(S[1][1]) (deg.)\n" +
                 "".join(f"{fi:.6e}, {20*np.log10(abs(si)):.12e}, {np.degrees(np.angle(si)):.12e}\n" for fi, si in zip(f, s)))
    ff, ss = s11io.read_palace_csv(p)
    assert np.allclose(ff, f * 1e9) and np.allclose(ss, s, atol=1e-9)

def test_write_then_read_round_trip(tmp_path):
    f = np.linspace(2e9, 3e9, 5); s = 0.1 * np.exp(1j * np.linspace(0, 3, 5))
    s11io.write_touchstone(tmp_path / "x.s1p", f, s, "lumped-port S11")
    ff, ss = s11io.read_touchstone(tmp_path / "x.s1p")
    assert np.allclose(ff, f) and np.allclose(ss, s)
