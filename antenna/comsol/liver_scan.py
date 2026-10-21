"""Liver-start scan on the idealised model, Physics-Controlled Mesh only (autoMeshSize index; no custom size nodes).
usage: [LIVER_GRID=f0,f1,df in GHz] [LIVER_MESH_ONLY=1] python liver_scan.py <tag> <value_mm,value_mm,...> [idx] [start|margin|<any params.Wen2021 field>]  (margin varies liver_margin: liver box and air box grow with it; a field name scans that dimension; `set` takes cases like n_helix_steps=13+helix_tip_bar=1;n_helix_steps=13)
liver_start_from_paddle is the distance from the paddle end (x = L1 = 17 mm) to the liver face; negative values put the liver
face before the paddle end (the FEP tube begins at x = L1, so for negative values the liver touches the bare board).
Every case first passes guard() (helix vias drawable, analysis/via_rules.py) or the run stops. LIVER_MESH_ONLY=1 builds and meshes
each case, prints elements and minimum element quality, and solves nothing (no CSV written).
Frequencies 2.30-2.70 GHz step 0.05 (includes 2.45 and 2.50). results/liver_scan_<tag>.csv: start, n_elem, solve_s, f_Hz, re, im."""
import os, sys, time, csv, dataclasses
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, ".."))
import mph, build_comsol as B
import params
from analysis.via_rules import presolve_problems, jlc_via_surcharge
BASE = params.JLC if os.environ.get("LIVER_BASE") == "JLC" else params.P   # LIVER_BASE=JLC scans around the JLCPCB stack instead of Wen's
P = BASE

def case_params(s0, vary):
    if vary == "set":  # s0 like "n_helix_steps=13+helix_tip_bar=1": several fields at once
        kv = dict(a.split("=") for a in str(s0).split("+"))
        def conv(k, v):  # bool, tuple of floats written like 3.9/3.9/3.9 (per-layer eps), or the field's own type
            cur = getattr(P, k)
            if isinstance(cur, bool): return v in ("1", "True", "true")
            if isinstance(cur, tuple): return tuple(float(x) for x in v.split("/"))
            return type(cur)(v)
        p = dataclasses.replace(P, **{k: conv(k, v) for k, v in kv.items()})
    else:
        field = {"start": "liver_start_from_paddle", "margin": "liver_margin"}.get(vary, vary)  # any Wen2021 field name works
        p = dataclasses.replace(P, **{field: type(getattr(P, field))(s0)})
    return p

def guard(p):
    """Stop before any COMSOL work when the helix vias cannot be drawn (pad off the board, hole >= via diameter, spacing)."""
    probs = presolve_problems(p)
    if probs:
        raise SystemExit("guard: not solving:\n  " + "\n  ".join(probs))
    print(f"guard OK: helix via hole {p.helix_drill} mm / via diameter {p.helix_pad} mm, JLCPCB surcharge "
          f"{jlc_via_surcharge(p.helix_drill, p.helix_pad)}, arm_miter_join {p.arm_miter_join}", flush=True)

def mesh_only(c, tag, cases, idx, g0, g1, dg):
    for s0, p in cases:
        m, jm = B.new_model(c, "dry_%s" % tag)
        comp, geom = B.build_geometry(jm, p); geom.run(); B.add_physics(jm, comp, p)
        B.add_study(jm, g0 * 1e9, g1 * 1e9, dg * 1e9)
        mesh = B.add_mesh(comp, idx); assert mesh.isAutomatic(); mesh.run()
        st = mesh.stat()
        print("MESH", s0, "elements", int(mesh.getNumElem()), "min quality %.4f" % st.getMinQuality(), "mean quality %.4f" % st.getMeanQuality(), flush=True)
        c.remove(m)

def main(tag, starts, idx=6, vary="start"):
    g0, g1, dg = (float(x) for x in os.environ.get("LIVER_GRID", "2.3,2.7,0.05").split(","))  # GHz
    cases = [(s0, case_params(s0, vary)) for s0 in starts]
    for _, p in cases: guard(p)
    dry = os.environ.get("LIVER_MESH_ONLY") == "1"
    out = os.path.join(HERE, "..", "results", f"liver_scan_{tag}.csv")
    if not dry and os.path.exists(out):
        raise SystemExit(f"not overwriting {out}: choose a new tag")
    c = mph.start(cores=int(os.environ.get("GATE_COMSOL_CORES", "6")))
    if dry:
        return mesh_only(c, tag, cases, idx, g0, g1, dg)
    with open(out, "w", newline="") as fh:
        w = csv.writer(fh); w.writerow(["start_mm", "n_elem", "solve_s", "f_Hz", "re", "im"])
        for s0 in starts:
            p = dict(cases)[s0]
            m, jm = B.new_model(c, "liver_%s_%d" % (tag, len(str(s0))))
            comp, geom = B.build_geometry(jm, p); geom.run(); B.add_physics(jm, comp, p)
            B.add_study(jm, g0 * 1e9, g1 * 1e9, dg * 1e9)
            mesh = B.add_mesh(comp, idx); assert mesh.isAutomatic(); mesh.run(); n = int(mesh.getNumElem())
            t = time.time(); jm.study("std1").run(); dt = time.time() - t
            f = np.atleast_1d(np.asarray(m.evaluate("freq", unit="Hz"), dtype=float)).ravel()
            sp = np.atleast_1d(m.evaluate("emw.S11")).ravel().astype(complex)
            for a, b in zip(f, sp): w.writerow([s0, n, round(dt, 1), a, b.real, b.imag])
            fh.flush()
            print("LIVER start", s0, "elements", n, "solve", round(dt), "s | f GHz:", " ".join("%.2f" % (x / 1e9) for x in f), flush=True)
            print("   S11 dB:", " ".join("%.2f" % (20 * np.log10(abs(x))) for x in sp), flush=True)
            c.remove(m)

if __name__ == "__main__":
    a = sys.argv[1:]
    main(a[0], a[1].split(";") if a[3:4] == ["set"] else [float(x) for x in a[1].split(",")], int(a[2]) if len(a) > 2 else 6, a[3] if len(a) > 3 else "start")
