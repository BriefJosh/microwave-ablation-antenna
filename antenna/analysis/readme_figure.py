"""Figure and table for the thesis repository README (final baseline set, 2026-10-12).
usage: python analysis/readme_figure.py -> results/wen2021_baseline_s11_comparison.png and results/mesh_and_cost_table.md
Curves: COMSOL idealised mesh ladder (idx 9-5), COMSOL full fidelity (idx 7), Palace 400 and 300 um, paper digitised Fig. 7(a). Every number comes from the data files in results/."""
import os, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); RES = os.path.join(HERE, "..", "results"); sys.path.insert(0, os.path.join(HERE, ".."))
from analysis import s11io, scan_dips

LADDER = [("9", "liver_scan_base_i9", "liver_margin=30"), ("8", "liver_scan_base_i8", "liver_margin=30"), ("7", "liver_scan_helix_tip", "n_helix_steps=13+helix_tip_bar=1"),
          ("6", "liver_scan_base_i6", "liver_margin=30"), ("5", "liver_scan_base_i5", "liver_margin=30")]

def figure(with_jlc=False, out="wen2021_baseline_s11_comparison.png"):
    """with_jlc adds the JLCPCB-stack curve; the thesis-repo README figure is made without it until the JLCPCB runs are final."""
    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
    plt.rcParams.update({"font.family": "serif", "font.size": 9, "axes.linewidth": 0.8})
    fig, ax = plt.subplots(figsize=(7.4, 6.0)); cols = ["#9ecae1", "#6baed6", "#4292c6", "#2171b5", "#08306b"]
    for (idx, tag, key), col in zip(LADDER, cols):
        c = scan_dips.load(os.path.join(RES, tag + ".csv"))[key]
        ax.plot(c["f"] / 1e9, c["db"], "-o", ms=3, lw=1.1, color=col, label=f"COMSOL, mesh index {idx} ({c['n'] // 1000}k elements)")
    f, s = s11io.read_comsol_csv(os.path.join(RES, "comsol_baseline13t_tbc_i7.csv")); ax.plot(f / 1e9, 20 * np.log10(abs(s)), "--^", ms=4, lw=1.1, color="#009E73", label="COMSOL, index 7, with copper loss and real vias")
    f, s = s11io.read_palace_csv(os.path.join(RES, "palace_sweep_c400_port-S.csv")); ax.plot(f / 1e9, 20 * np.log10(abs(s)), "-s", ms=4, lw=1.1, color="#D55E00", label="Palace, 400 µm cells (153k elements)")
    f, s = s11io.read_palace_csv(os.path.join(RES, "palace_c300_points_port-S.csv")); ax.plot(f / 1e9, 20 * np.log10(abs(s)), "--D", ms=5, lw=1.1, color="black", label="Palace, 300 µm cells (172k elements, 4 points)")
    ps = np.loadtxt(os.path.join(RES, "paper_fig7a_sim.csv"), delimiter=",", skiprows=2); ax.plot(ps[:, 0] / 1e9, ps[:, 1], ":", color="0.4", lw=1.8, label="Wen et al. 2021, Fig. 7(a), digitised")
    if with_jlc:
        c = scan_dips.load(os.path.join(RES, "liver_scan_jlc_nominal_i6.csv"))["liver_margin=30"]
        ax.plot(c["f"] / 1e9, c["db"], "-o", ms=4, lw=2.0, color="#CC79A7", label="COMSOL, JLCPCB 7628 stack (nominal), mesh index 6")
    ax.axhline(-10, color="0.8", lw=0.8); ax.axvline(2.45, color="0.8", lw=0.8); ax.set_xlim(2.30, 2.60); ax.set_ylim(-36, 0)
    ax.set_xlabel("Frequency (GHz)"); ax.set_ylabel("|S11| (dB)"); ax.grid(alpha=0.2); ax.legend(fontsize=7, loc="upper center", bbox_to_anchor=(0.5, -0.13), ncol=2, frameon=False)
    fig.tight_layout(); fig.savefig(os.path.join(RES, out), dpi=200)

def table():
    n = {i: scan_dips.load(os.path.join(RES, t + ".csv"))[k] for i, t, k in LADDER}; n5 = n["5"]["n"]
    rows = ["| Curve | Solver and mesh setting | Elements | Unknowns | Effective element size (relative to COMSOL index 5) | Sweep points | Run time | Peak memory |", "|---|---|---|---|---|---|---|---|"]
    for i in ("9", "8", "7", "6", "5"):
        c = n[i]; rows.append(f"| COMSOL index {i} | COMSOL 6.1, Physics-Controlled Mesh, index {i} | {c['n']:,} | not recorded | {(n5 / c['n']) ** (1 / 3):.2f} | 13 | {c['t']:.0f} s for the sweep | not logged |")
    rows.append("| COMSOL index 7, copper loss and real vias | same, copper as thickness-aware boundary, 90 via cylinders | 232,555 | not recorded | 1.16 | 13 | 593 s for the sweep | not logged |")
    rows.append("| Palace 400 µm | Palace 0.18.1, order 2, refined cell size 400 µm | 153,782 | 1,101,132 | n/a | 13 | 98 min for the sweep (6 min per point), 3 MPI ranks | 3.9 GB in the largest rank; total not logged |")
    rows.append("| Palace 300 µm | Palace 0.18.1, order 2, refined cell size 300 µm, GMRES restart 50 | 171,567 | 1,228,090 | 0.96 (relative to Palace 400 µm) | 4 | about 11.5 min per point, one point per process | about 9.6 GB used by WSL, up to 10.9 GB at the end of a solve |")
    note = ("\nHardware: laptop with a Ryzen 5 7530U (6 cores) and 13.9 GB RAM; Palace ran in WSL with an 11 GB limit and 4 GB swap. COMSOL 6.1 used 6 cores. "
            "Palace's linear solver: GMRES, tolerance 1e-6, p-multigrid with a complex coarse solve (SuperLU). COMSOL's: GMRES with a geometric multigrid preconditioner (default). "
            "The Palace element counts are those of the solver, which adds interface elements to the 152,587 and 170,117 tetrahedra in the mesh files. "
            "Effective element size is (elements)^(-1/3) relative to the reference mesh; the cell-size setting of Palace changes it by only about 3% per step because the thin layers and vias limit the mesh.\n")
    open(os.path.join(RES, "mesh_and_cost_table.md"), "w", encoding="utf-8").write("\n".join(rows) + "\n" + note); print("\n".join(rows))

if __name__ == "__main__":
    if "--with-jlc" in sys.argv: figure(True, "wen_gate_s11_with_jlcpcb.png")
    else: figure(); table()
