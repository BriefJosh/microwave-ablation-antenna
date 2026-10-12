"""Mesh-convergence overlay: COMSOL idealised baseline at five mesh indices, Palace at 400 um (13 points) and 300 um (4 points), and the paper's digitised Fig. 7(a).
usage: python analysis/overlay_convergence.py -> results/convergence_overlay.png and a printed table"""
import os, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); RES = os.path.join(HERE, "..", "results"); sys.path.insert(0, os.path.join(HERE, ".."))
from analysis import s11io, scan_dips

def main():
    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(9, 5.2))
    ladder = [("9", "liver_scan_base_i9", "liver_margin=30"), ("8", "liver_scan_base_i8", "liver_margin=30"), ("7", "liver_scan_helix_tip", "n_helix_steps=13+helix_tip_bar=1"),
              ("6", "liver_scan_base_i6", "liver_margin=30"), ("5", "liver_scan_base_i5", "liver_margin=30")]
    cols = plt.cm.viridis(np.linspace(0.05, 0.85, len(ladder))); print("| curve | elements | dip GHz | depth dB | S11 at 2.45 GHz dB |\n|---|---|---|---|---|")
    for (idx, tag, key), col in zip(ladder, cols):
        c = scan_dips.load(os.path.join(RES, tag + ".csv"))[key]; fd, dd, _ = scan_dips.dip(c["f"], c["db"]); k = int(np.argmin(abs(c["f"] - 2.45e9)))
        ax.plot(c["f"] / 1e9, c["db"], "-o", ms=3, lw=1.2, color=col, label=f"COMSOL idx {idx} ({c['n'] // 1000}k elements)"); print(f"| COMSOL idx {idx} | {c['n']} | {fd / 1e9:.4f} | {dd:.1f} | {c['db'][k]:.2f} |")
    for name, path, st, mk in (("Palace 400 um (153k)", "palace_sweep_c400_port-S.csv", "s", "tab:red"), ("Palace 300 um (172k)", "palace_c300_points_port-S.csv", "D", "k")):
        f, s = s11io.read_palace_csv(os.path.join(RES, path)); db = 20 * np.log10(abs(s)); ax.plot(f / 1e9, db, "--" + st, ms=5, lw=1.2, color=mk, label=name)
        i = int(np.argmin(db)); k = int(np.argmin(abs(f - 2.45e9)))
        if 0 < i < len(db) - 1:
            A, B, C = db[i - 1], db[i], db[i + 1]; d = .5 * (A - C) / (A - 2 * B + C); print(f"| {name} | | {f[i] / 1e9 + d * .025:.4f} | {B - .25 * (A - C) * d:.1f} | {db[k]:.2f} |")
    ps = np.loadtxt(os.path.join(RES, "paper_fig7a_sim.csv"), delimiter=",", skiprows=2); ax.plot(ps[:, 0] / 1e9, ps[:, 1], ":", color="0.45", lw=1.8, label="paper Fig. 7(a), digitised")
    ax.axvline(2.45, color="0.7", lw=0.8); ax.axhline(-10, color="0.8", lw=0.8); ax.set_xlim(2.3, 2.6); ax.set_ylim(-36, 0); ax.set_xlabel("Frequency (GHz)"); ax.set_ylabel("|S11| (dB)"); ax.grid(alpha=0.25); ax.legend(fontsize=7.5, loc="lower right", ncol=2)
    ax.set_title("Wen 2021 baseline, 50 ohm lumped-port S11: mesh sequence (idealised model)", fontsize=10); fig.tight_layout(); fig.savefig(os.path.join(RES, "convergence_overlay.png"), dpi=140)

if __name__ == "__main__":
    main()
