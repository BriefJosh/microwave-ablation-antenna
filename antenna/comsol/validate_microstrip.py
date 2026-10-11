"""Plain 50 ohm microstrip port validation (see tests/test_comsol_microstrip_port.py). Same port recipe as build_comsol.add_physics:
uniform lumped ports (E along z, height = substrate, width = trace) sitting INSIDE the model between the trace edge and the ground edge,
air behind both ends, scattering boundary on the outer box, PEC sheet copper, FR4 loss as sigma_eq."""
import os, sys
import numpy as np
import jpype
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, ".."))
import mph, build_comsol as B
from params import P
import stackup

H = P.h_top + P.h_bond + P.h_bot          # 0.665 mm
W, L, SW = P.W6, 30.0, 10.0               # trace width, line length, substrate width

def run(mesh_index=5, freqs=(2.0e9, 2.25e9, 2.45e9, 2.75e9, 3.0e9), save=None, box=(15.0, 10.0), client=None):
    """box = (half-width y, margin above/below z) of the air box in mm. A client may be passed in (mph.start works once per process)."""
    client = client or mph.start(cores=int(os.environ.get("GATE_COMSOL_CORES", "4")))
    m, jm = B.new_model(client, "microstrip_port_validation")
    try:
        comp = jm.component().create("comp1", True)
        geom = comp.geom().create("geom1", 3); geom.lengthUnit("mm")
        for nm in ("cu", "p1", "p2", "dom_air", "dom_sub"): geom.selection().create(f"csel_{nm}", "CumulativeSelection")
        def blk(tag, x0, y0, z0, x1, y1, z1, sel):
            b = geom.create(tag, "Block"); b.set("pos", [float(x0), float(y0), float(z0)]); b.set("size", [float(x1 - x0), float(y1 - y0), float(z1 - z0)]); b.set("contributeto", sel)
        blk("air", -5, -box[0], -box[1], L + 5, box[0], H + box[1], "csel_dom_air"); blk("sub", 0, -SW / 2, 0, L, SW / 2, H, "csel_dom_sub")
        def sheet(tag, z, x0, y0, x1, y1):
            wp = geom.create(tag, "WorkPlane"); wp.set("quickplane", "xy"); wp.set("quickz", float(z)); wp.set("unite", True)
            r = wp.geom().create("r", "Rectangle"); r.set("pos", [float(x0), float(y0)]); r.set("size", [float(x1 - x0), float(y1 - y0)]); wp.set("contributeto", "csel_cu")
        sheet("gnd", 0.0, 0, -SW / 2, L, SW / 2); sheet("trace", H, 0, -W / 2, L, W / 2)
        for tag, x, sel in (("wp_p1", 0.0, "csel_p1"), ("wp_p2", L, "csel_p2")):
            wp = geom.create(tag, "WorkPlane"); wp.set("planetype", "quick"); wp.set("quickplane", "yz"); wp.set("quickx", float(x)); wp.set("unite", True)
            r = wp.geom().create("r", "Rectangle"); r.set("pos", [float(-W / 2), 0.0]); r.set("size", [float(W), float(H)]); wp.set("contributeto", sel)
        d = geom.create("dif_air", "Difference"); d.selection("input").set(["air"]); d.selection("input2").set(["sub"]); d.set("keepsubtract", True)
        geom.run()
        for name, sel, er, sg in (("air", "geom1_csel_dom_air_dom", 1.0, 0.0),
                                  ("fr4", "geom1_csel_dom_sub_dom", P.eps_fr4, stackup.sigma_eq(P.eps_fr4, P.tand_fr4))):
            mt = comp.material().create(f"mat_{name}", "Common"); pg = mt.propertyGroup("def")
            pg.set("relpermittivity", [repr(er)]); pg.set("relpermeability", ["1"]); pg.set("electricconductivity", [repr(sg)]); mt.selection().named(sel)
        emw = comp.physics().create("emw", "ElectromagneticWaves", "geom1")
        ext = [int(i) for i in emw.feature("pec1").selection().entities()]
        ents = lambda t: [int(i) for i in comp.selection(t).entities()]
        p1, p2, cu = ents("geom1_csel_p1_bnd"), ents("geom1_csel_p2_bnd"), ents("geom1_csel_cu_bnd")
        pec = emw.create("pec_cu", "PerfectElectricConductor", 2); pec.selection().set(cu)
        sbc = emw.create("sbc", "Scattering", 2); sbc.selection().set(sorted(set(ext) - set(p1) - set(p2) - set(cu)))
        for tag, ids, on in (("lp1", p1, True), ("lp2", p2, False)):
            lp = emw.create(tag, "LumpedPort", 2); lp.selection().set(ids)
            lp.set("PortType", "Uniform"); lp.set("hPort", f"{H}[mm]"); lp.set("wPort", f"{W}[mm]")
            lp.set("E_src", "userdef"); lp.set("E", ["0", "0", "1"]); lp.set("SourceType", "Power"); lp.set("P0", "1[W]"); lp.set("Zref", "50[ohm]")
            lp.set("PortExcitation", "on" if on else "off")
        mesh = comp.mesh().create("mesh1"); mesh.automatic(True); mesh.autoMeshSize(int(mesh_index))
        std = jm.study().create("std1"); st = std.create("freq", "Frequency")
        st.set("plist", " ".join(f"{f:g}" for f in freqs)); st.set("punit", "Hz")
        mesh.run(); std.run()
        f = np.atleast_1d(np.asarray(m.evaluate("freq", unit="Hz"), dtype=float)).ravel()
        s11 = np.atleast_1d(m.evaluate("emw.S11")).ravel().astype(complex); s21 = np.atleast_1d(m.evaluate("emw.S21")).ravel().astype(complex)
        if save and not os.path.exists(save): m.save(save)
        return f, s11, s21
    finally:
        client.remove(m)

if __name__ == "__main__":
    f, s11, s21 = run(int(sys.argv[1]) if len(sys.argv) > 1 else 5)
    for a, b, c in zip(f, s11, s21): print("%.2f GHz  S11 %.1f dB  S21 %.2f dB" % (a / 1e9, 20 * np.log10(abs(b)), 20 * np.log10(abs(c))))
