from dataclasses import dataclass
from analysis import metrics

TOL_FMIN_VS_COMSOL = 0.02; TOL_BAND_VS_COMSOL = 0.03; TOL_FMIN_VS_PAPER = 0.05
F_PAPER = 2.45e9; DB_AT_PAPER = -15.0; TOL_REFINE = 0.01; TOL_POWER = 0.05

@dataclass
class Check:
    name: str
    passed: bool
    detail: str

def evaluate(curves, refine, logs_ok, power_err):
    rows = []
    ref = curves["comsol"]; fr, _ = metrics.s11_min(*ref); br = metrics.band_edges(*ref)
    for name in ("elmer", "palace"):
        if name not in curves: continue
        fm, dbm = metrics.s11_min(*curves[name])
        e = metrics.rel(fm, fr)
        rows.append(Check(f"{name}: S11-min frequency vs COMSOL", e <= TOL_FMIN_VS_COMSOL, f"{fm/1e9:.4f} vs {fr/1e9:.4f} GHz ({100*e:.2f}%)"))
        b = metrics.band_edges(*curves[name])
        if b is None or br is None:
            rows.append(Check(f"{name}: -10 dB band edges vs COMSOL", False, f"no -10 dB crossing (solver {b}, COMSOL {br})"))
        else:
            e1, e2 = metrics.rel(b[0], br[0]), metrics.rel(b[1], br[1])
            rows.append(Check(f"{name}: -10 dB band edges vs COMSOL", max(e1, e2) <= TOL_BAND_VS_COMSOL,
                              f"[{b[0]/1e9:.4f}, {b[1]/1e9:.4f}] vs [{br[0]/1e9:.4f}, {br[1]/1e9:.4f}] GHz"))
    for name in ("comsol", "elmer", "palace"):
        if name not in curves: continue
        fm, _ = metrics.s11_min(*curves[name]); e = metrics.rel(fm, F_PAPER); d = metrics.db_at(*curves[name], F_PAPER)
        rows.append(Check(f"{name}: S11-min within 5% of 2.45 GHz", e <= TOL_FMIN_VS_PAPER, f"{fm/1e9:.4f} GHz ({100*e:.2f}%)"))
        rows.append(Check(f"{name}: S11 at 2.45 GHz below -15 dB", d < DB_AT_PAPER, f"{d:.2f} dB"))
    for name, (a, b) in refine.items():
        e = metrics.rel(b, a)
        rows.append(Check(f"{name}: mesh refinement shift < 1%", e < TOL_REFINE, f"{a/1e9:.4f} -> {b/1e9:.4f} GHz ({100*e:.2f}%)"))
    for name, ok in logs_ok.items():
        rows.append(Check(f"{name}: solver converged (log scan)", ok, "clean" if ok else "non-convergence found"))
    for name, e in power_err.items():
        rows.append(Check(f"{name}: power balance within 5%", e <= TOL_POWER, f"{100*e:.2f}%"))
    return rows
