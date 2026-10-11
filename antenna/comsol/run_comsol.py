"""Build, mesh and solve the COMSOL gate model; write S11 (lumped port, 50 ohm, 1 W incident) and a power-balance line.
usage: python run_comsol.py <mesh_size_index 1..9> <f0_Hz> <f1_Hz> <df_Hz> <tag> [liver_margin_mm|-] [ideal|tbc]
Outputs (results/): comsol_<tag>.csv (freq_Hz,re,im), comsol_<tag>.s1p, comsol_<tag>_info.json; model saved as
comsol/mph/wen2021_gate_<tag>.mph (a new name every time; an existing file is never overwritten)."""
import json, os, sys, time
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, ".."))
import mph, build_comsol
from analysis import s11io

RES = os.path.join(HERE, "..", "results")

def run(size, f0, f1, df, tag, margin=None, variant="ideal"):
    """variant: 'ideal' (PEC sheets, wall fence) or 'tbc' (copper as Transition Boundary Condition faces, real via cylinders)."""
    client = mph.start(cores=int(os.environ.get("GATE_COMSOL_CORES", "6")))
    m, jm = build_comsol.new_model(client, f"wen_gate_{tag}")
    tbc = variant == "tbc"
    comp, geom = build_comsol.build_geometry(jm, liver_margin=margin, real_vias=tbc); geom.run()
    emw = build_comsol.add_physics(jm, comp, copper="tbc" if tbc else "pec")
    mesh = build_comsol.add_mesh(comp, size); build_comsol.add_study(jm, f0, f1, df)
    t = time.time(); mesh.run(); t_mesh = time.time() - t
    n_elem = int(mesh.getNumElem())
    t = time.time(); jm.study("std1").run(); t_solve = time.time() - t
    f = np.atleast_1d(np.asarray(m.evaluate("freq", unit="Hz"), dtype=float)).ravel()
    s11 = np.atleast_1d(m.evaluate("emw.S11")).ravel().astype(complex)
    # absorbed power: volume integral of the dissipation density over every field domain
    num = jm.result().numerical().create("int_q", "IntVolume")
    doms = sorted(set(sum([build_comsol._ents(comp, f"geom1_csel_dom_{n}_dom") for n in ("air", "liver", "fep", "board")], [])))
    num.selection().set(doms); num.set("expr", "emw.Qh"); num.set("unit", "W")
    q = np.asarray(num.getReal(), dtype=float).ravel()
    q = q.reshape(-1)[:len(f)] if q.size >= len(f) else q
    ndof = None
    try: ndof = int(jm.sol("sol1").getNumDof()) if hasattr(jm.sol("sol1"), "getNumDof") else None
    except Exception: pass
    info = dict(tag=tag, variant=variant, mesh_size_index=size, n_elem=n_elem, ndof=ndof, mesh_s=round(t_mesh, 1), solve_s=round(t_solve, 1),
                n_freq=int(len(f)), liver_margin=margin, p_abs_over_pinc=[float(x) for x in q], one_minus_s11sq=[float(1 - abs(s) ** 2) for s in s11])
    os.makedirs(RES, exist_ok=True)
    np.savetxt(os.path.join(RES, f"comsol_{tag}.csv"), np.c_[f, s11.real, s11.imag], delimiter=",", header="freq_Hz,re,im", comments="% ")
    s11io.write_touchstone(os.path.join(RES, f"comsol_{tag}.s1p"), f, s11, f"COMSOL 6.1 lumped-port S11, mesh size index {size}")
    json.dump(info, open(os.path.join(RES, f"comsol_{tag}_info.json"), "w"), indent=1)
    os.makedirs(os.path.join(HERE, "mph"), exist_ok=True); out = os.path.join(HERE, "mph", f"wen2021_gate_{tag}.mph")
    if os.path.exists(out): out = out.replace(".mph", f"_{int(time.time())}.mph")
    m.save(out); client.remove(m)
    return info

if __name__ == "__main__":
    a = sys.argv[1:]
    info = run(int(a[0]), float(a[1]), float(a[2]), float(a[3]), a[4], float(a[5]) if len(a) > 5 and a[5] != "-" else None, a[6] if len(a) > 6 else "ideal")
    print(json.dumps({k: v for k, v in info.items() if not k.startswith(("p_abs", "one_minus"))}, indent=1))
    print("p_abs/p_inc  vs 1-|S11|^2:", info["p_abs_over_pinc"][:3], info["one_minus_s11sq"][:3])
