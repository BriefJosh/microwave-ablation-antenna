"""Is the step in |E| at the liver face (x = x_liver0) physics or a model defect? Loads a solved model, samples Ex, Ey, Ez just before and after
the face and along x, checks the boundary conditions (analysis/interface_check.py), lists any emw feature sitting on the face, discards the model.
usage: python liver_face_check.py [model.mph] [solnum] [tag]      (default: mph/wen2021_gate_sweep11_tbc_m6.mph, solnum 5, tag sweep11_tbc_m6)
Output: results/liver_face_check_<tag>.json (pairs, features, slice settings), .csv (profiles), .png (|E| and components against x, log axis)."""
import os, sys, json
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); G = os.path.join(HERE, "..")
sys.path.insert(0, HERE); sys.path.insert(0, G)
import mph
import params
from params import derived
from analysis.interface_check import eps_complex, continuity

EXPR = ("emw.Ex", "emw.Ey", "emw.Ez", "emw.normE")

def eval_points(model, pts, solnum):
    """Complex values of EXPR at pts (mm, the model's length unit). Shape (4, n)."""
    res = model.java.result()
    for kind, t in (("numerical", "lfpev"), ("dataset", "lfcut")):
        try: getattr(res, kind)().remove(t)
        except Exception: pass
    ds = [str(t) for t in res.dataset().tags()][0]
    cp = res.dataset().create("lfcut", "CutPoint3D"); cp.set("data", ds)
    for k, ax in enumerate("xyz"): cp.set("point" + ax, " ".join(f"{v:.9g}" for v in pts[:, k]))
    pe = res.numerical().create("lfpev", "EvalPoint"); pe.set("data", "lfcut")
    for k, e in enumerate(EXPR): pe.setIndex("expr", e, k)
    pe.set("solnum", [str(int(solnum))])
    n = len(pts)
    v = (np.array(pe.getReal()).ravel() + 1j * np.array(pe.getImag()).ravel()).reshape(len(EXPR), n)   # stacked: all points of expr 0, then expr 1, ...
    res.numerical().remove("lfpev"); res.dataset().remove("lfcut")
    return v

def face_boundaries(jm, x0):
    g = jm.component("comp1").geom("geom1"); V = np.array(g.getVertexCoord()); adj = g.getAdj(2, 0)
    return [b + 1 for b in range(len(adj)) if np.allclose(V[0, [int(i) - 1 for i in adj[b]]], x0, atol=1e-6)]

def features_on(jm, faces):
    out = {}
    emw = jm.physics("emw")
    for t in emw.feature().tags():
        f = emw.feature(str(t))
        try:
            if int(f.selection().dimension()) != 2: continue
            hit = sorted(set(int(i) for i in f.selection().entities()) & set(faces))
            if hit: out[str(t)] = hit
        except Exception:
            pass
    return out

def slice_settings(jm):
    out = []
    for pg in jm.result().tags():
        for ft in jm.result(str(pg)).feature().tags():
            f = jm.result(str(pg)).feature(str(ft))
            if "slice" not in str(f.getType()).lower(): continue
            s = {"plot": f"{pg}/{ft}"}
            for k in ("quickplane", "quickpmethod", "quickznumber", "quickz", "expr", "rangecoloractive", "rangecolormax"):
                try: s[k] = str(f.getString(k))
                except Exception: pass
            out.append(s)
    return out

def main(a):
    path = a[0] if a else os.path.join(HERE, "mph", "wen2021_gate_sweep11_tbc_m6.mph")
    solnum = int(a[1]) if len(a) > 1 else 5; tag = a[2] if len(a) > 2 else "sweep11_tbc_m6"
    p = params.P; d = derived(p); x0 = d["x_liver0"]; zt = d["z_top"]
    c = mph.start(cores=int(os.environ.get("GATE_COMSOL_CORES", "6")))
    m = c.load(path); jm = m.java
    try:
        f_all = np.atleast_1d(np.asarray(m.evaluate("freq", unit="Hz"), float)).ravel(); f = float(f_all[solnum - 1])
        bb = [float(v) for v in jm.component("comp1").geom("geom1").getBoundingBox()]   # xmin, xmax, ymin, ymax, zmin, zmax (mm)
        zmid = 0.5 * (bb[4] + bb[5])
        ec = eps_complex(p.eps_liver, p.sigma_liver, f); efep = eps_complex(p.eps_fep, 0.0, f)
        yfep = p.W4 / 2 + p.fep_t
        # (label, y, z, eps below the face, eps above it): (a) air | liver outside the tube, (b) FEP wall and (c) inside the board as controls
        probes = [("a: air|liver, y 2.3, slice z", 2.3, zmid, 1.0, ec), ("a: air|liver, y 3, slice z", 3.0, zmid, 1.0, ec),
                  ("a: air|liver, y 5, slice z", 5.0, zmid, 1.0, ec), ("a: air|liver, y 0, z 1.5", 0.0, 1.5, 1.0, ec),
                  ("a: air|liver, y 0, z 3", 0.0, 3.0, 1.0, ec),
                  ("b: control, FEP wall, y 1.95, slice z", 1.95, zmid, efep, efep),
                  ("c: control, board, y 0, slice z", 0.0, zmid, complex(p.eps_fr4), complex(p.eps_fr4))]
        dx = 0.02
        pts = np.array([(x0 - dx, y, z) for _, y, z, _, _ in probes] + [(x0 + dx, y, z) for _, y, z, _, _ in probes])
        v = eval_points(m, pts, solnum); n = len(probes)
        pairs = []
        for k, (lab, y, z, ea, eb) in enumerate(probes):
            Ea, Eb = v[:3, k], v[:3, n + k]
            r = continuity(Ea[None], Eb[None], ea, eb)
            pairs.append({"probe": lab, "y_mm": y, "z_mm": z, "x_below_mm": x0 - dx, "x_above_mm": x0 + dx,
                          "abs_E_below": float(np.linalg.norm(Ea)), "abs_E_above": float(np.linalg.norm(Eb)),
                          "abs_Ex_Ey_Ez_below": [float(t) for t in np.abs(Ea)], "abs_Ex_Ey_Ez_above": [float(t) for t in np.abs(Eb)],
                          **{kk: float(vv[0]) for kk, vv in r.items()}})
        # profiles along x across the face
        xs = np.round(np.arange(25.0, 50.0 + 1e-9, 0.1), 6)
        lines = [("y 2.3, slice z", 2.3, zmid), ("y 3, slice z", 3.0, zmid), ("y 0, z 1.5", 0.0, 1.5), ("y 0, slice z (inside board)", 0.0, zmid)]
        P = np.vstack([np.column_stack([xs, np.full_like(xs, y), np.full_like(xs, z)]) for _, y, z in lines])
        pv = eval_points(m, P, solnum).reshape(len(EXPR), len(lines), len(xs))
        faces = face_boundaries(jm, x0)
        summ = {"model": os.path.abspath(path), "solnum": solnum, "freq_GHz": f / 1e9, "x_liver0_mm": x0, "bbox_mm": bb, "slice_z_mm_quick_midplane": zmid,
                "z_top_mm": zt, "fep_outer_y_mm": yfep, "eps_c_liver": [ec.real, ec.imag], "abs_eps_c_liver": abs(ec),
                "pairs": pairs, "face_boundaries": faces, "emw_features_on_face": features_on(jm, faces), "slice_plots": slice_settings(jm),
                "nan_points": int(np.sum(~np.isfinite(pv))) + int(np.sum(~np.isfinite(v)))}
    finally:
        c.remove(m)                                                   # loaded read-only: nothing is saved
    base = os.path.join(G, "results", f"liver_face_check_{tag}")
    json.dump(summ, open(base + ".json", "w"), indent=1)
    hdr = ["x_mm"] + [f"{lab} | abs {e}" for lab, _, _ in lines for e in ("Ex", "Ey", "Ez", "normE")]
    cols = [xs] + [np.abs(pv[k, j]) for j in range(len(lines)) for k in range(len(EXPR))]
    np.savetxt(base + ".csv", np.column_stack(cols), delimiter=",", header=",".join(hdr), comments="")
    plot(base + ".png", xs, pv, lines, summ)
    print(json.dumps(summ, indent=1), flush=True); print("wrote", os.path.abspath(base + ".png"))

def plot(out, xs, pv, lines, s):
    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
    fig, axs = plt.subplots(1, len(lines), figsize=(4.2 * len(lines), 3.8), dpi=150, sharey=False)
    cols = {"Ex": "#b2182b", "Ey": "#2166ac", "Ez": "#1b7837", "normE": "0.15"}
    for j, (lab, _, _) in enumerate(lines):
        ax = axs[j]
        for k, e in enumerate(("Ex", "Ey", "Ez", "normE")):
            ax.semilogy(xs, np.abs(pv[k, j]), color=cols[e], lw=2.2 if e == "normE" else 1.3, label=("|E|" if e == "normE" else f"|{e}|"))
        ax.axvline(s["x_liver0_mm"], color="0.4", ls="--", lw=1); ax.axhline(1000, color="0.6", ls=":", lw=1)
        ax.text(s["x_liver0_mm"] + 0.3, ax.get_ylim()[0] * 1.5, "liver face", fontsize=7, color="0.3")
        ax.set_title(lab, fontsize=8.5); ax.set_xlabel("x (mm)"); ax.grid(alpha=0.25, which="both")
    axs[0].set_ylabel("field (V/m), 1 W incident"); axs[0].legend(fontsize=7, frameon=False)
    fig.suptitle(f"Wen stack, sweep11 TBC mesh 6, {s['freq_GHz']:.3f} GHz: field across the liver face (dotted: the 1000 V/m colour cap)", fontsize=9)
    fig.tight_layout(); fig.savefig(out)

if __name__ == "__main__":
    main(sys.argv[1:])
