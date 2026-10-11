"""Summarise the COMSOL diagnostic scans (convergence_*.csv, liver_scan_*.csv): dip position and depth per case, and one overview figure.
Dip = lowest |S11| grid point, refined by a parabola through it and its two neighbours (only when it is interior to the grid).
The grids are 0.05 GHz apart, so a parabola dip is good to a few MHz and its depth is a lower bound on the true depth.
usage: python analysis/scan_dips.py  -> prints a markdown table, writes results/diagnosis_s11_overview.png"""
import os, csv, glob
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); RES = os.path.join(HERE, "..", "results")

def load(path):
    rows = list(csv.DictReader(open(path)))
    if not rows: return {}  # a scan still solving has written only the header, or nothing
    key = next(k for k in rows[0] if k in ("idx", "start_mm"))
    cases = {}
    for r in rows:
        cases.setdefault(r[key], []).append(r)
    out = {}
    for k, rr in cases.items():
        f = np.array([float(r["f_Hz"]) for r in rr]); s = np.array([float(r["re"]) + 1j * float(r["im"]) for r in rr])
        out[k] = dict(f=f, db=20 * np.log10(np.abs(s)), n=int(rr[0]["n_elem"]), t=float(rr[0]["solve_s"]))
    return out

def dip(f, db):
    i = int(np.argmin(db))
    if 0 < i < len(db) - 1:
        a, b, c = db[i - 1], db[i], db[i + 1]; den = a - 2 * b + c
        if den > 0:
            d = 0.5 * (a - c) / den; return f[i] + d * (f[1] - f[0]), b - 0.25 * (a - c) * d, True
    return f[i], db[i], False

def db_at(f, db, f0):
    j = int(np.argmin(abs(f - f0)));  return db[j] if abs(f[j] - f0) < 1e6 else float("nan")

def main():
    files = sorted(glob.glob(os.path.join(RES, "convergence_*.csv")) + glob.glob(os.path.join(RES, "liver_scan_*.csv")))
    print("| file | case | elements | solve s | dip GHz | dip dB | S11 @2.45 GHz dB | interior |\n|---|---|---|---|---|---|---|---|")
    data = {}
    for p in files:
        name = os.path.basename(p)[:-4]; data[name] = load(p)
        for k, v in data[name].items():
            fd, dd, ok = dip(v["f"], v["db"]); s245 = db_at(v["f"], v["db"], 2.45e9)
            print(f"| {name} | {k} | {v['n']} | {v['t']:.0f} | {fd / 1e9:.3f} | {dd:.1f} | {'' if np.isnan(s245) else format(s245, '.1f')} | {'yes' if ok else 'edge'} |")
    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
    fig, ax = plt.subplots(1, 2, figsize=(12, 4.6))
    ps = np.loadtxt(os.path.join(RES, "paper_fig7a_sim.csv"), delimiter=",", skiprows=2)
    for a in ax: a.plot(ps[:, 0] / 1e9, ps[:, 1], color="0.6", ls="--", lw=1.5, label="paper Fig. 7(a) sim (digitised)")
    st = data.get("liver_scan_start", {})
    if "20.0" in st: ax[0].plot(st["20.0"]["f"] / 1e9, st["20.0"]["db"], "k-o", ms=4, label="baseline (12 steps, idx 6)")
    for k, c in (("11.0", "tab:blue"), ("13.0", "tab:red")):
        d = data.get("liver_scan_dim_n_helix_steps", {}).get(k)
        if d is not None: ax[0].plot(d["f"] / 1e9, d["db"], "-o", color=c, ms=4, label=f"{int(float(k))} helix steps (idx 7)")
    ax[0].set_title("Helix step count (via pairs per row = steps + 1)")
    for k, c in (("0.0", "tab:orange"), ("10.0", "tab:green"), ("30.0", "tab:purple"), ("-10.0", "tab:brown")):
        if k in st: ax[1].plot(st[k]["f"] / 1e9, st[k]["db"], "-o", color=c, ms=4, label=f"liver starts {int(float(k))} mm past paddle")
    if "20.0" in st: ax[1].plot(st["20.0"]["f"] / 1e9, st["20.0"]["db"], "k-o", ms=4, label="liver starts 20 mm (baseline)")
    ax[1].set_title("Liver start position (idx 6)")
    for a in ax:
        a.axvline(2.45, color="r", lw=0.8, alpha=0.5); a.set_xlabel("frequency (GHz)"); a.set_ylabel("S11 (dB)"); a.set_xlim(2.3, 2.7); a.set_ylim(-35, 0); a.grid(alpha=0.3); a.legend(fontsize=7)
    fig.suptitle("COMSOL 6.1, idealised model, 1 W, 50 ohm lumped-port S11 (red line = 2.45 GHz)", fontsize=10)
    fig.tight_layout(); fig.savefig(os.path.join(RES, "diagnosis_s11_overview.png"), dpi=130)

if __name__ == "__main__":
    main()
