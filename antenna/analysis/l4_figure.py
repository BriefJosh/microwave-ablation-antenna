"""Figure for the findings note: S11 of the JLCPCB stack as the straight arm L4 grows (6, 7, 8, 9 mm; L3 lengthened with it), with the -10 dB line and the 2.45 GHz target.
usage: python analysis/l4_figure.py [out.png]   data: results/liver_scan_jlc_nominal_i6.csv, liver_scan_jlc_L4_i6.csv, liver_scan_jlc_L4_9_i6.csv"""
import os, sys
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
HERE = os.path.dirname(os.path.abspath(__file__)); RES = os.path.join(HERE, "..", "results"); sys.path.insert(0, HERE)
import scan_dips

SRC = [("L4 = 6.0 mm (earlier run)", "liver_scan_jlc_nominal_i6", "liver_margin=30", "#CC79A7"),
       ("L4 = 7.0 mm, L3 = 71.5", "liver_scan_jlc_L4_i6", "L4=7.0+L3=71.5", "#7fcdbb"),
       ("L4 = 8.0 mm, L3 = 72.5", "liver_scan_jlc_L4_i6", "L4=8.0+L3=72.5", "#2ca25f"),
       ("L4 = 9.0 mm, L3 = 73.5", "liver_scan_jlc_L4_9_i6", "L4=9.0+L3=73.5", "#006d2c")]

def main(out):
    fig, ax = plt.subplots(figsize=(7.5, 4.4), dpi=150)
    for label, tag, key, col in SRC:
        d = scan_dips.load(os.path.join(RES, tag + ".csv"))[key]
        ax.plot(d["f"] / 1e9, d["db"], "-o", ms=3.5, lw=1.6, color=col, label=label)
    ax.axhline(-10, color="0.4", ls=":", lw=1); ax.text(2.595, -9.6, "-10 dB", ha="right", va="bottom", fontsize=8, color="0.3")
    ax.axvline(2.45, color="0.4", ls="--", lw=1); ax.text(2.4515, -31.5, "2.45 GHz", fontsize=8, color="0.3")
    ax.set_xlabel("Frequency (GHz)"); ax.set_ylabel("|S11| (dB)"); ax.set_xlim(2.30, 2.60); ax.set_ylim(-33, 0)
    ax.set_title("JLCPCB 7628 stack: S11 against straight-arm length L4 (COMSOL index 6, liver)", fontsize=9.5)
    ax.legend(fontsize=8, loc="lower left", frameon=False); ax.grid(alpha=0.25)
    fig.tight_layout(); fig.savefig(out); print("wrote", os.path.abspath(out))

if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "..", "results", "l4_retune_s11.png"))
