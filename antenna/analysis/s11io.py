import numpy as np
_UNIT = {"HZ": 1.0, "KHZ": 1e3, "MHZ": 1e6, "GHZ": 1e9}

def read_touchstone(path):
    unit, fmt, rows = "GHZ", "MA", []
    for line in open(path):
        line = line.split("!")[0].strip()
        if not line: continue
        if line.startswith("#"):
            t = line[1:].upper().split()
            unit = next((x for x in t if x in _UNIT), unit); fmt = next((x for x in t if x in ("MA", "DB", "RI")), fmt)
            continue
        rows.append([float(x) for x in line.split()[:3]])
    a = np.array(rows); f = a[:, 0] * _UNIT[unit]
    if fmt == "RI": s = a[:, 1] + 1j * a[:, 2]
    else:
        mag = a[:, 1] if fmt == "MA" else 10 ** (a[:, 1] / 20)
        s = mag * np.exp(1j * np.radians(a[:, 2]))
    return f, s

def read_palace_csv(path):
    a = np.loadtxt(path, delimiter=",", skiprows=1, ndmin=2)
    return a[:, 0] * 1e9, 10 ** (a[:, 1] / 20) * np.exp(1j * np.radians(a[:, 2]))

def read_comsol_csv(path):
    a = np.loadtxt(path, delimiter=",", comments=("%", "#"), skiprows=1, ndmin=2)
    return a[:, 0], a[:, 1] + 1j * a[:, 2]

def write_touchstone(path, f_hz, s11, comment):
    with open(path, "w") as fh:
        fh.write(f"! {comment}\n# HZ S RI R 50\n")
        for f, s in zip(f_hz, s11):
            fh.write(f"{f:.10g} {s.real:.12g} {s.imag:.12g}\n")
