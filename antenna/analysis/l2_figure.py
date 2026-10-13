"""Figure for the findings note: left, S11 of the JLCPCB stack with L4 = 8.0 mm as the wide pad L2 grows (11.5 to 14.5 mm); right, the retuned layout (L2 = 14.5 mm)
at permittivity 4.4, nominal (4.4 / 4.23 / 4.4) and 3.9 in all layers, with the 2.45 GHz target and the -10 dB line.
usage: python analysis/l2_figure.py [out.png]"""
import os, sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
HERE = os.path.dirname(os.path.abspath(__file__)); RES = os.path.join(HERE, "..", "results"); sys.path.insert(0, HERE)
import scan_dips

L2 = [("L2 = 11.5 mm", "liver_scan_jlc_L4_8_L2_i6", "L4=8.0+L3=72.5+L2=11.5", "#fdb863"),
      ("L2 = 12.5 mm", "liver_scan_jlc_L4_i6", "L4=8.0+L3=72.5", "#f1a340"),
      ("L2 = 13.5 mm", "liver_scan_jlc_L4_8_L2_i6", "L4=8.0+L3=72.5+L2=13.5", "#e08214"),
      ("L2 = 14.5 mm", "liver_scan_jlc_L4_8_L2_145_i6", "L4=8.0+L3=72.5+L2=14.5", "#7f3b08")]
EPS = [("eps 4.4 in all layers", "liver_scan_jlc_best_eps_i6", "L4=8.0+L3=72.5+L2=14.5+eps_layers=4.4/4.4/4.4", "#2166ac", "--"),
       ("nominal 4.4 / 4.23 / 4.4", "liver_scan_jlc_L4_8_L2_145_i6", "L4=8.0+L3=72.5+L2=14.5", "#7f3b08", "-"),
       ("eps 3.9 in all layers", "liver_scan_jlc_best_eps39_i6", "L4=8.0+L3=72.5+L2=14.5+eps_layers=3.9/3.9/3.9", "#b2182b", ":")]

def panel(ax, series, title, xmax):
    for s in series:
        label, tag, key, col = s[:4]; ls = s[4] if len(s) > 4 else "-"
        d = scan_dips.load(os.path.join(RES, tag + ".csv"))[key]
        ax.plot(d["f"] / 1e9, d["db"], ls, marker="o", ms=3.2, lw=1.6, color=col, label=label)
    ax.axhline(-10, color="0.4", ls=":", lw=1); ax.axvline(2.45, color="0.4", ls="--", lw=1)
    ax.text(2.4515, -29.5, "2.45 GHz", fontsize=8, color="0.3")
    ax.set_xlim(2.30, xmax); ax.set_ylim(-31, 0); ax.set_xlabel("Frequency (GHz)"); ax.set_title(title, fontsize=9)
    ax.legend(fontsize=7.5, loc="lower left", frameon=False); ax.grid(alpha=0.25)

def main(out):
    fig, axs = plt.subplots(1, 2, figsize=(11, 4.2), dpi=150, sharey=True)
    panel(axs[0], L2, "L4 = 8.0 mm: S11 against the wide-pad length L2 (nominal stack)", 2.60)
    panel(axs[1], EPS, "Retuned layout (L4 8.0, L2 14.5, L3 72.5): S11 against permittivity", 2.75)
    axs[0].set_ylabel("|S11| (dB)")
    fig.tight_layout(); fig.savefig(out); print("wrote", os.path.abspath(out))

if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "..", "results", "l2_retune_s11.png"))
