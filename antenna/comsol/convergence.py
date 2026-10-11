"""Mesh-convergence study on the idealised model with the Physics-Controlled Mesh only (autoMeshSize index; no custom size nodes).
usage: python convergence.py <tag> <idx,idx,...> [lossy] [edges]
Frequencies 2.50-2.70 GHz step 0.05; results/convergence_<tag>.csv has one row per (index, frequency): idx, n_elem, solve_s, f_Hz, re, im.
'lossy' turns on ResolveWaveInLossyMedia, 'edges' turns on RefineConductiveEdges (both are properties of the RF interface's mesh control)."""
import os, sys, time, csv
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, ".."))
import mph, build_comsol as B

def main(tag, indices, lossy=False, edges=False):
    c = mph.start(cores=int(os.environ.get("GATE_COMSOL_CORES", "6")))
    m, jm = B.new_model(c, f"conv_{tag}")
    comp, geom = B.build_geometry(jm); geom.run(); emw = B.add_physics(jm, comp)
    mc = emw.prop("MeshControl")
    if lossy: mc.set("ResolveWaveInLossyMedia", "1")
    if edges: mc.set("RefineConductiveEdges", "1")
    freqs = np.arange(2.50e9, 2.70e9 + 1, 5e7); B.add_study(jm, 2.5e9, 2.7e9, 5e7)
    mesh = B.add_mesh(comp, indices[0]); assert mesh.isAutomatic()
    out = os.path.join(HERE, "..", "results", f"convergence_{tag}.csv")
    with open(out, "w", newline="") as fh:
        w = csv.writer(fh); w.writerow(["idx", "n_elem", "solve_s", "f_Hz", "re", "im"])
        for idx in indices:
            mesh.autoMeshSize(int(idx)); mesh.run(); n = int(mesh.getNumElem())
            t = time.time(); jm.study("std1").run(); dt = time.time() - t
            f = np.atleast_1d(np.asarray(m.evaluate("freq", unit="Hz"), dtype=float)).ravel()
            s = np.atleast_1d(m.evaluate("emw.S11")).ravel().astype(complex)
            for a, b in zip(f, s): w.writerow([idx, n, round(dt, 1), a, b.real, b.imag])
            fh.flush(); print("CONV idx", idx, "elements", n, "solve", round(dt), "s | S11 dB:", " ".join("%.2f" % (20 * np.log10(abs(x))) for x in s), flush=True)
    c.remove(m)

if __name__ == "__main__":
    a = sys.argv[1:]
    main(a[0], [int(x) for x in a[1].split(",")], "lossy" in a[2:], "edges" in a[2:])
