"""Impedance along the SICL from a COMSOL solution: V(x) = integral Ez from the inner strip to the top plate, I(x) = circulation of H around the strip,
then analysis/line_fit.py gives Z0, gamma and the load impedance at the line end (all at one frequency).
usage:
  python impedance_profile.py load <model.mph> <tag> [Wen|JLC] [solnum]      # solved model, load and discard (never saved)
  python impedance_profile.py solve <tag> <case> [idx] [freq_GHz]            # build the case (LIVER_BASE=JLC for the JLCPCB stack; case like L4=8.0+L3=72.5),
                                                                              # solve ONE frequency, sample, discard
Output: results/impedance_profile_<tag>.csv (x, V, I, Zin per plane) and results/impedance_profile_<tag>.json (fit)."""
import os, sys, json, dataclasses
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); G = os.path.join(HERE, "..")
sys.path.insert(0, HERE); sys.path.insert(0, G)
import mph, build_comsol as B
import params
from params import derived
from analysis.field_sampling import plan, integrate
from analysis.line_fit import fit_line, zin_transform

def sample(model, p, solnum=None, dataset=None, step=1.0, **loop):
    d = derived(p); jm = model.java
    xs = np.arange(d["x_sicl0"] + 1.0, d["x_sicl1"] - 0.5 + 1e-9, step)
    pl = plan(xs, d["z_inner"], d["z_top"], **loop)
    P = pl["points"]                                              # CutPoint3D takes the model's length unit (mm) in this model; not metres
    res = jm.result()
    for t in ("zcut", "zpev"):
        try:
            if t == "zcut": res.dataset().remove(t)
            else: res.numerical().remove(t)
        except Exception: pass
    dsets = [str(t) for t in res.dataset().tags()]
    ds = dataset or dsets[0]
    cp = res.dataset().create("zcut", "CutPoint3D"); cp.set("data", ds)
    cp.set("pointx", " ".join(f"{v:.9g}" for v in P[:, 0])); cp.set("pointy", " ".join(f"{v:.9g}" for v in P[:, 1])); cp.set("pointz", " ".join(f"{v:.9g}" for v in P[:, 2]))
    pe = res.numerical().create("zpev", "EvalPoint"); pe.set("data", "zcut")
    for k, e in enumerate(("emw.Ez", "emw.Hy", "emw.Hz")): pe.setIndex("expr", e, k)
    if solnum is not None:
        pe.set("solnum", [str(int(solnum))])
    n = len(P)
    re = np.array(pe.getReal()).ravel().reshape(3, n); im = np.array(pe.getImag()).ravel().reshape(3, n)   # EvalPoint stacks the expressions: all points of Ez, then Hy, then Hz
    f = np.asarray(model.evaluate("freq", unit="Hz")).ravel()
    vals = re + 1j * im                                           # shape (3, npts)
    bad = int(np.sum(~np.isfinite(vals)))
    out = integrate(pl, vals[0], vals[1], vals[2])
    out["V"] = out["V"] * 1e-3; out["I"] = out["I"] * 1e-3        # fields are V/m and A/m, the plan's weights are in mm
    return out, bad, f

def report(tag, out, bad, p, f_hz, model=None):
    V, I, x = out["V"], out["I"], out["x"]
    if (V * np.conj(I)).real[0] < 0: I = -I                       # power flows +x at the source end; fix the arbitrary current sign
    Z = V / I
    r = fit_line(x, V, I); d = derived(p)
    z_end = zin_transform(r["z_end"], r["z0"], r["gamma"], 0.0)
    s = {"tag": tag, "f_GHz": float(np.ravel(f_hz)[0]) / 1e9, "nan_points": bad,
         "Z0_ohm": [r["z0"].real, r["z0"].imag], "gamma_per_mm": [r["gamma"].real, r["gamma"].imag],
         "beta_rad_per_mm": r["gamma"].imag, "lambda_g_mm": 2 * np.pi / r["gamma"].imag, "neff": r["gamma"].imag / (2 * np.pi * float(np.ravel(f_hz)[0]) / 2.99792458e11),
         "Zin_at_line_start_ohm": [r["z_start"].real, r["z_start"].imag], "Z_at_line_end_ohm": [r["z_end"].real, r["z_end"].imag],
         "x_start_mm": float(x[0]), "x_end_mm": float(x[-1]),
         "power_ratio_check": float(np.abs((V * np.conj(I)).real).max() / max(np.abs((V * np.conj(I)).real).min(), 1e-30))}
    base = os.path.join(G, "results", f"impedance_profile_{tag}")
    np.savetxt(base + ".csv", np.column_stack([x, V.real, V.imag, I.real, I.imag, Z.real, Z.imag]), delimiter=",",
               header="x_mm,V_re,V_im,I_re,I_im,Zin_re_ohm,Zin_im_ohm", comments="")
    json.dump(s, open(base + ".json", "w"), indent=1)
    print(json.dumps(s, indent=1), flush=True)

def main(a):
    mode = a[0]
    c = mph.start(cores=int(os.environ.get("GATE_COMSOL_CORES", "6")))
    if mode == "load":
        path, tag = a[1], a[2]; base = a[3] if len(a) > 3 else "Wen"; sn = int(a[4]) if len(a) > 4 else None
        p = params.JLC if base == "JLC" else params.P
        m = c.load(path)
        out, bad, f = sample(m, p, sn)
        report(tag, out, bad, p, f, m)
        c.remove(m)
    else:
        tag, case = a[1], a[2]; idx = int(a[3]) if len(a) > 3 else 6; fg = float(a[4]) if len(a) > 4 else 2.45
        P0 = params.JLC if os.environ.get("LIVER_BASE") == "JLC" else params.P
        kv = dict(s.split("=") for s in case.split("+")) if case not in ("", "base") else {}
        def conv(k, v):
            cur = getattr(P0, k)
            if isinstance(cur, bool): return v in ("1", "True", "true")
            if isinstance(cur, tuple): return tuple(float(x) for x in v.split("/"))
            return type(cur)(v)
        p = dataclasses.replace(P0, **{k: conv(k, v) for k, v in kv.items()})
        m, jm = B.new_model(c, "zprof_" + tag)
        comp, geom = B.build_geometry(jm, p); geom.run(); B.add_physics(jm, comp, p)
        B.add_study(jm, fg * 1e9, fg * 1e9, 1e7)
        mesh = B.add_mesh(comp, idx); assert mesh.isAutomatic(); mesh.run(); print("elements", int(mesh.getNumElem()), flush=True)
        jm.study("std1").run()
        s11 = np.atleast_1d(m.evaluate("emw.S11")).ravel().astype(complex)[0]
        print("S11 dB at %.3f GHz: %.2f; port Zin %s ohm" % (fg, 20 * np.log10(abs(s11)), 50 * (1 + s11) / (1 - s11)), flush=True)
        out, bad, f = sample(m, p)
        report(tag, out, bad, p, f, m)
        c.remove(m)

if __name__ == "__main__":
    main(sys.argv[1:])
