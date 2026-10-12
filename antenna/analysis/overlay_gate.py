"""Overlay of the open solver (Palace) with COMSOL (idealised and full fidelity) and the paper's digitised Fig. 7(a), all on the same Fig. 4b baseline.
usage: python analysis/overlay_gate.py -> results/gate_overlay_palace_comsol.png and a printed table"""
import os, sys, csv
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); RES = os.path.join(HERE, "..", "results"); sys.path.insert(0, os.path.join(HERE, ".."))
from analysis import s11io, scan_dips

def dip(f, db):
    fd, dd, ok = scan_dips.dip(f, db); return fd / 1e9, dd

def main():
    curves = {}
    f, s = s11io.read_palace_csv(os.path.join(RES, "palace_sweep_c400_port-S.csv")); curves["Palace v0.18.1, order 2, 400 um cells (PEC sheets, wall fence)"] = (f, 20 * np.log10(abs(s)))
    c = scan_dips.load(os.path.join(RES, "liver_scan_helix_tip.csv"))["n_helix_steps=13+helix_tip_bar=1"]; curves["COMSOL 6.1, idealised (same geometry)"] = (c["f"], c["db"])
    f, s = s11io.read_comsol_csv(os.path.join(RES, "comsol_baseline13t_tbc_i7.csv")); curves["COMSOL 6.1, full fidelity (copper thickness + loss, real vias)"] = (f, 20 * np.log10(abs(s)))
    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(8.6, 5)); sty = [("tab:red", "-o"), ("tab:blue", "-s"), ("tab:green", "-^")]
    print("| curve | dip GHz | dip dB | S11 at 2.45 GHz dB |\n|---|---|---|---|")
    for (name, (f, db)), (col, mk) in zip(curves.items(), sty):
        ax.plot(f / 1e9, db, mk, color=col, ms=4, lw=1.4, label=name); fd, dd = dip(f, db)
        i = int(np.argmin(abs(f - 2.45e9))); print(f"| {name} | {fd:.4f} | {dd:.1f} | {db[i]:.2f} |")
    ps = np.loadtxt(os.path.join(RES, "paper_fig7a_sim.csv"), delimiter=",", skiprows=2); ax.plot(ps[:, 0] / 1e9, ps[:, 1], "--", color="0.55", lw=1.4, label="paper Fig. 7(a) simulation (digitised, pixel-limited)")
    ax.axvline(2.45, color="k", lw=0.8, alpha=0.4); ax.set_xlim(2.3, 2.6); ax.set_ylim(-35, 0); ax.set_xlabel("frequency (GHz)"); ax.set_ylabel("S11 (dB)"); ax.grid(alpha=0.3); ax.legend(fontsize=7.5, loc="lower right")
    ax.set_title("Wen 2021 baseline (13 steps + tip bar), 50 ohm lumped-port S11, 0.025 GHz grid", fontsize=10); fig.tight_layout(); fig.savefig(os.path.join(RES, "gate_overlay_palace_comsol.png"), dpi=140)

if __name__ == "__main__":
    main()
