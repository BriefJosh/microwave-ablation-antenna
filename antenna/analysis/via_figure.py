"""Helix via candidates on the retuned layout (L4 8.0, L2 14.5, L3 72.5 mm, JLCPCB nominal stack 4.4 / 4.23 / 4.4, liver, 50 ohm port,
COMSOL index 6): one table row per run and one S11 overlay, with the pre-2026-10-21 square-ended reference (helix via 0.2 / 0.40 mm).
usage: python analysis/via_figure.py   -> results/via_candidates_table.md, results/via_candidates_s11.png
Margins are signed: positive = 2.45 GHz inside the -10 dB band by that much, negative = outside by that much."""
import csv, os, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); RES = os.path.join(HERE, "..", "results"); sys.path[:0] = [HERE, os.path.join(HERE, "..")]
import metrics
from via_rules import jlc_via_surcharge

F0 = 2.45e9
REF = ("Square ends (before 2026-10-21), 0.2 / 0.40", "liver_scan_jlc_L4_8_L2_145_i6", "L4=8.0+L3=72.5+L2=14.5", 0.2, 0.40, "0.5", "--")
RUNS = [("Mitered, 0.2 / 0.40", "liver_scan_jlc_best_via_0p2_0p40_miter_i6", 0.2, 0.40, "#7f3b08", "-"),
        ("Mitered, 0.2 / 0.45", "liver_scan_jlc_best_via_0p2_0p45_miter_i6", 0.2, 0.45, "#2166ac", "-"),
        ("Mitered, 0.3 / 0.45", "liver_scan_jlc_best_via_0p3_0p45_miter_i6", 0.3, 0.45, "#1b7837", "-"),
        ("Mitered, 0.4 / 0.50", "liver_scan_jlc_best_via_0p4_0p50_miter_i6", 0.4, 0.50, "#b2182b", "-")]

def summarize(f_hz, s11):
    f = np.asarray(f_hz, float); s = np.asarray(s11, complex)
    fd, dd = metrics.s11_min(f, s)
    band = metrics.band_edges(f, s)
    sre, sim = np.interp(F0, f, s.real), np.interp(F0, f, s.imag); s0 = sre + 1j * sim
    r = dict(dip_ghz=fd / 1e9, depth_db=float(dd), s11_245_db=metrics.db_at(f, s, F0), zin_245=complex(50 * (1 + s0) / (1 - s0)),
             band_lo_ghz=None, band_hi_ghz=None, width_mhz=None, margin_lo_mhz=None, margin_hi_mhz=None)
    if band:
        lo, hi = band
        r.update(band_lo_ghz=lo / 1e9, band_hi_ghz=hi / 1e9, width_mhz=(hi - lo) / 1e6, margin_lo_mhz=(F0 - lo) / 1e6, margin_hi_mhz=(hi - F0) / 1e6)
    return r

def load(tag, key=None):
    """(f, s11, elements, solve_s) of one case; key picks the case in a multi-case CSV."""
    rows = list(csv.DictReader(open(os.path.join(RES, tag + ".csv"))))
    if key is not None: rows = [r for r in rows if r["start_mm"] == key]
    if not rows: return None
    f = np.array([float(r["f_Hz"]) for r in rows]); s = np.array([float(r["re"]) + 1j * float(r["im"]) for r in rows])
    return f, s, int(rows[0]["n_elem"]), float(rows[0]["solve_s"])

def _f(x, fmt): return "-" if x is None else format(x, fmt)

def main():
    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
    cases = [(REF[0], load(REF[1], REF[2]), REF[3], REF[4], REF[5], REF[6], REF[1])]
    cases += [(lab, load(tag) if os.path.exists(os.path.join(RES, tag + ".csv")) else None, h, d, c, ls, tag) for lab, tag, h, d, c, ls in RUNS]
    head = ("| Case (hole / via diameter, mm) | JLCPCB surcharge | Elements | Solve (s) | Dip (GHz) | Depth (dB) | S11 at 2.45 GHz (dB) "
            "| -10 dB band (GHz) | Width (MHz) | Margin of 2.45 GHz (low / high, MHz) | Port Zin at 2.45 GHz (ohm) | CSV |")
    lines = ["Helix via candidates, 2026-10-21. Retuned layout L4 8.0, L2 14.5, L3 72.5 mm, w_inner 0.5 mm; JLCPCB nominal stack 4.4 / 4.23 / 4.4; "
             "liver; 50 ohm port; COMSOL physics-controlled mesh index 6; one mesh per case; 0.025 GHz grid (reference 2.30-2.75 GHz, new runs 2.30-2.60 GHz). "
             "Margins signed: negative = 2.45 GHz outside the band by that much.", "", head, "|" + "---|" * 12]
    fig, ax = plt.subplots(figsize=(8.2, 4.6), dpi=160)
    for lab, data, h, d, col, ls, tag in cases:
        if data is None:
            lines.append(f"| {lab} | {jlc_via_surcharge(h, d)} | not run | | | | | | | | | `{tag}.csv` |"); continue
        f, s, n, t = data; r = summarize(f, s); z = r["zin_245"]
        band = "-" if r["band_lo_ghz"] is None else f"{r['band_lo_ghz']:.4f} to {r['band_hi_ghz']:.4f}"
        lines.append(f"| {lab} | {jlc_via_surcharge(h, d)} | {n} | {t:.0f} | {r['dip_ghz']:.4f} | {r['depth_db']:.1f} | {r['s11_245_db']:.2f} | {band} "
                     f"| {_f(r['width_mhz'], '.0f')} | {_f(r['margin_lo_mhz'], '.1f')} / {_f(r['margin_hi_mhz'], '.1f')} | {z.real:.1f} {'+' if z.imag >= 0 else '-'} j{abs(z.imag):.1f} | `{tag}.csv` |")
        ax.plot(f / 1e9, metrics.db(s), ls, marker="o", ms=3, lw=1.6, color=col, label=lab + " mm")
    ax.axhline(-10, color="0.4", ls=":", lw=1); ax.axvline(2.45, color="0.4", ls="--", lw=1)
    ax.set_xlim(2.30, 2.60); ax.set_ylim(-32, 0); ax.grid(alpha=0.25)
    ax.set_xlabel("Frequency (GHz)"); ax.set_ylabel("|S11| (dB)")
    ax.set_title("Helix via (hole / via diameter) on the retuned layout, JLCPCB nominal stack, liver, COMSOL index 6", fontsize=8.5)
    ax.legend(fontsize=7.5, frameon=False, loc="lower left")
    fig.tight_layout(); png = os.path.join(RES, "via_candidates_s11.png"); fig.savefig(png)
    md = os.path.join(RES, "via_candidates_table.md"); open(md, "w", encoding="utf-8").write("\n".join(lines) + "\n")
    print("wrote", os.path.abspath(md)); print("wrote", os.path.abspath(png)); print("\n".join(lines))

if __name__ == "__main__":
    main()
