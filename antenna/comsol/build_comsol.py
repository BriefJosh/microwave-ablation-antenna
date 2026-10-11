"""COMSOL 6.1 (RF Module) reference model of the Wen 2021 gate geometry, built from params.py / shapes.py via the Java API.
Same solver-variant geometry as gds2palace: copper = zero-thickness PEC faces, fence = two continuous walls, vias =
8-gon PEC solids, FR4 and FEP loss as the same equivalent conductivity (stackup.sigma_eq), lumped port on the x = 0 face.
Run with the system Python (mph + COMSOL). Never saves over an existing .mph."""
import os, sys
import jpype
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, ".."))
from params import P, derived, dielectric_layers
import shapes, stackup

NG = 8   # via polygon sides (the same as the gds2palace solver variant)

def _layer_polys(polys, layer):
    return [q for q in polys if q.layer == layer and not q.hole], [q for q in polys if q.layer == layer and q.hole]

def _poly_feature(wp_geom, tag, pts):
    f = wp_geom.create(tag, "Polygon"); f.set("type", "solid")
    f.set("x", [float(x) for x, _ in pts]); f.set("y", [float(y) for _, y in pts]); return f

def _workplane(geom, tag, z, polys, holes, contribute):
    wp = geom.create(tag, "WorkPlane"); wp.set("quickplane", "xy"); wp.set("quickz", float(z)); wp.set("unite", True)
    wg = wp.geom(); names = []
    for i, q in enumerate(polys):
        _poly_feature(wg, f"p{i}", q.pts); names.append(f"p{i}")
    if len(names) > 1:
        u = wg.create("uni", "Union"); u.selection("input").set(names); u.set("intbnd", False); last = "uni"
    else:
        last = names[0]
    if holes:
        hn = []
        for i, q in enumerate(holes):
            _poly_feature(wg, f"h{i}", q.pts); hn.append(f"h{i}")
        d = wg.create("dif", "Difference"); d.selection("input").set([last]); d.selection("input2").set(hn)
    if contribute: wp.set("contributeto", contribute)
    return wp

def build_geometry(jm, p=P, liver_margin=None, real_vias=False):
    """real_vias=True: the 90 fence vias and the feed/helix vias are true circular cylinders (not walls and 8-gons)."""
    d = derived(p); zt, zi = d["z_top"], d["z_inner"]
    m = p.liver_margin if liver_margin is None else liver_margin
    big = m + 5
    polys0, vias0 = shapes.build(p)
    polys, vias = (polys0, vias0) if real_vias else shapes.solver_variant(polys0, vias0, p, NG)
    comp = jm.component().create("comp1", True)
    geom = comp.geom().create("geom1", 3); geom.lengthUnit("mm")
    DL = dielectric_layers(p); one = len(DL) == 1                       # Wen: one FR4 block (tag "board"); layered: board0, board1, board2
    sel_board = ["dom_board"] if one else [f"dom_board{i}" for i in range(len(DL))]
    for nm in ("cu_top", "cu_inner", "cu_bottom", "cu_via", "port", "dom_air", "dom_liver", "dom_fep", *sel_board):
        geom.selection().create(f"csel_{nm}", "CumulativeSelection")
    hw = p.W4 / 2
    def blk(tag, x0, y0, z0, x1, y1, z1, contribute=None):
        b = geom.create(tag, "Block"); b.set("pos", [x0, y0, z0]); b.set("size", [x1 - x0, y1 - y0, z1 - z0])
        if contribute: b.set("contributeto", contribute)
        return b
    # domains: big air box = gds2palace's background; liver brick; FEP tube; FR4 board
    blk("air", -p.air_margin, -(hw + m), -big, d["x_tip"] + m, hw + m, zt + big, "csel_dom_air")
    blk("liver", d["x_liver0"], -(hw + m), -m, d["x_tip"] + m, hw + m, zt + m, "csel_dom_liver")
    # the sleeve reaches back to the liver face when the liver starts before the SICL, so liver never touches bare board
    blk("fep", min(d["x_sicl0"], d["x_liver0"]), -(hw + p.fep_t), -p.fep_t, d["x_tip"] + p.fep_t, hw + p.fep_t, zt + p.fep_t, "csel_dom_fep")
    bpoly = next(q for q in polys if q.layer == "BOARD"); btags = []
    for i, L in enumerate(DL):
        tag = "board" if one else f"board{i}"
        wb = geom.create(f"wp_{tag}", "WorkPlane"); wb.set("quickplane", "xy"); wb.set("quickz", float(L["z0"])); wb.set("unite", True)
        _poly_feature(wb.geom(), "b", bpoly.pts)
        eb = geom.create(tag, "Extrude"); eb.selection("input").set([f"wp_{tag}"]); eb.set("distance", [float(L["z1"] - L["z0"])]); eb.set("contributeto", f"csel_{sel_board[i]}")
        btags.append(tag)
    # vias as PEC solids
    vp, _ = _layer_polys(polys, "VIA")
    wv = geom.create("wp_via", "WorkPlane"); wv.set("quickplane", "xy"); wv.set("quickz", 0.0); wv.set("unite", True)
    if real_vias:
        for i, v in enumerate(vias):
            c_ = wv.geom().create(f"v{i}", "Circle"); c_.set("r", float(v.drill / 2)); c_.set("pos", [float(v.x), float(v.y)])
    else:
        for i, q in enumerate(vp): _poly_feature(wv.geom(), f"v{i}", q.pts)
    ev = geom.create("vias", "Extrude"); ev.selection("input").set(["wp_via"]); ev.set("distance", [zt]); ev.set("contributeto", "csel_cu_via")
    # copper faces
    for lay, z, csel in (("TOP", zt, "csel_cu_top"), ("INNER", zi, "csel_cu_inner"), ("BOTTOM", 0.0, "csel_cu_bottom")):
        add, holes = _layer_polys(polys, lay)
        _workplane(geom, f"wp_{lay.lower()}", z, add, holes, csel)
    # port face on the x = 0 plane: y in +-W6/2, z in [0, zt]
    wpp = geom.create("wp_port", "WorkPlane"); wpp.set("planetype", "quick"); wpp.set("quickplane", "yz"); wpp.set("quickx", 0.0)
    wpp.set("unite", True)
    r = wpp.geom().create("r", "Rectangle"); r.set("pos", [-p.W6 / 2, 0.0]); r.set("size", [p.W6, zt]); wpp.set("contributeto", "csel_port")
    # booleans (tools kept until their last use as an input)
    a = geom.create("dif_air", "Difference"); a.selection("input").set(["air"]); a.selection("input2").set(["liver", "fep", *btags]); a.set("keepsubtract", True)
    b = geom.create("dif_liver", "Difference"); b.selection("input").set(["liver"]); b.selection("input2").set(["fep", *btags]); b.set("keepsubtract", True)
    c = geom.create("dif_fep", "Difference"); c.selection("input").set(["fep"]); c.selection("input2").set(btags); c.set("keepsubtract", True)
    for tag in btags:
        e = geom.create(f"dif_{tag}", "Difference"); e.selection("input").set([tag]); e.selection("input2").set(["vias"]); e.set("keepsubtract", True)
    geom.run("fin") if False else None
    return comp, geom

def new_model(client, name):
    m = client.create(name); return m, m.java

def _ents(comp, tag): return [int(i) for i in comp.selection(tag).entities()]

def add_physics(jm, comp, p=P, full=False, copper="pec"):
    """full=True: real-copper model of build_full (one copper body selection, port between the plates 0.6825 mm).
    copper="pec": copper faces are perfect conductors. copper="tbc": copper faces carry a Transition Boundary Condition (copper
    conductivity and the real layer thickness, thick-layer option) and only the via walls are PEC."""
    d = derived(p); zt = d["z_top"]
    if full:
        from params import derived_full
        F = derived_full(p); zt = F["z_top_cu0"] - F["z_bot_cu1"]
    # materials: one per domain group; FR4/FEP loss as the same equivalent conductivity as the other solvers
    mats = (("air", "geom1_csel_dom_air_dom", 1.0, 0.0), ("liver", "geom1_csel_dom_liver_dom", p.eps_liver, p.sigma_liver),
            ("fep", "geom1_csel_dom_fep_dom", p.eps_fep, stackup.sigma_eq(p.eps_fep, p.tand_fep)),
            *((("fr4", "geom1_csel_dom_board_dom", p.eps_fr4, stackup.sigma_eq(p.eps_fr4, p.tand_fr4)),) if len(dielectric_layers(p)) == 1 else
              tuple((f"diel{i}", f"geom1_csel_dom_board{i}_dom", L["eps"], stackup.sigma_eq(L["eps"], L["tand"])) for i, L in enumerate(dielectric_layers(p)))))
    doms = []
    for name, sel, er, sg in mats:
        mt = comp.material().create(f"mat_{name}", "Common"); mt.label(name)
        pg = mt.propertyGroup("def")
        pg.set("relpermittivity", [repr(er)]); pg.set("relpermeability", ["1"]); pg.set("electricconductivity", [repr(sg)])
        mt.selection().named(sel); doms += _ents(comp, sel)
    emw = comp.physics().create("emw", "ElectromagneticWaves", "geom1")
    emw.selection().set(sorted(set(doms)))                 # via solids are PEC, not part of the field domain
    pec0 = emw.feature("pec1")
    ext = [int(i) for i in pec0.selection().entities()]     # default PEC sits on every exterior boundary
    port_b = _ents(comp, "geom1_csel_port_bnd")
    if full:
        # Classify from the geometry's own vertex data: an outer-box face has all its vertices in one of the six outer planes; every other
        # exterior boundary of the field domains is a copper surface (the copper bodies are excluded domains). Cumulative-selection and
        # Box-selection shortcuts both missed faces next to the port (Box limits are in metres, not mm).
        import numpy as np
        from params import derived_full as _df
        F = _df(p); m_ = p.liver_margin; big = m_ + 5; hw = p.W4 / 2
        lo = np.array([-p.air_margin, -(hw + m_), F["z_bot_cu0"] - big]); hi = np.array([d["x_tip"] + m_, hw + m_, F["z_top_cu1"] + big])
        g = comp.geom("geom1"); V = np.array(g.getVertexCoord()); adj = g.getAdj(2, 0)
        def on_outer(b):
            X = V[:, [int(v) - 1 for v in adj[b]]]
            return any(np.allclose(X[k], lo[k], atol=1e-6) or np.allclose(X[k], hi[k], atol=1e-6) for k in range(3))
        outer_faces = {b for b in ext if b not in port_b and on_outer(b)}
        via_b = []; cu_b = sorted((set(ext) - outer_faces - set(port_b)))
    else:
        via_b = _ents(comp, "geom1_csel_cu_via_bnd")
        cu_b = sorted(set(_ents(comp, "geom1_csel_cu_top_bnd") + _ents(comp, "geom1_csel_cu_inner_bnd") +
                          _ents(comp, "geom1_csel_cu_bottom_bnd") + via_b))
    # default pec1 (all exterior boundaries, selection not editable) stays; later features override it on their boundaries
    if copper == "tbc" and not full:
        faces = {n: _ents(comp, f"geom1_csel_cu_{n}_bnd") for n in ("top", "inner", "bottom")}
        allf = sorted(set(sum(faces.values(), [])))
        mt = comp.material().create("mat_cu", "Common"); mt.label("copper")
        mt.selection().geom("geom1", 2).set(allf)
        pg = mt.propertyGroup("def"); pg.set("relpermittivity", ["1"]); pg.set("relpermeability", ["1"]); pg.set("electricconductivity", [repr(p.sigma_cu)])
        for n, d_um in (("top", p.t_cu_outer * 1000), ("bottom", p.t_cu_outer * 1000), ("inner", p.t_cu_inner * 1000)):
            tb = emw.create(f"tbc_{n}", "TransitionBoundaryCondition", 2); tb.selection().set(faces[n])
            tb.set("d", f"{d_um:g}[um]"); tb.set("noCoupling", "1")      # copper is 13-26 skin depths thick at 2.45 GHz: thick-layer option
        pec = emw.create("pec_cu", "PerfectElectricConductor", 2); pec.selection().set(sorted(set(via_b)))
    else:
        pec = emw.create("pec_cu", "PerfectElectricConductor", 2); pec.selection().set(cu_b)
    # The air box extends air_margin behind the feed (x < 0), so the lumped port is an interior boundary sitting between the
    # ground-plane edge and the launch-strip edge. A port on the outer wall was rejected by COMSOL's equation compiler twice
    # (next to scattering boundaries; then "not between two conductive boundaries" once the wall was PEC).
    outer = outer_faces if full else set(ext) - set(port_b) - set(via_b) - set(cu_b)
    sbc = emw.create("sbc", "Scattering", 2); sbc.selection().set(sorted(outer))
    lp = emw.create("lport1", "LumpedPort", 2); lp.selection().set(port_b)
    lp.set("PortType", "Uniform"); lp.set("hPort", f"{zt}[mm]"); lp.set("wPort", f"{p.W6}[mm]")
    lp.set("E_src", "userdef"); lp.set("E", ["0", "0", "1"]); lp.set("SourceType", "Power"); lp.set("P0", "1[W]"); lp.set("Zref", "50[ohm]")
    return emw

def add_mesh(comp, size_index=4):
    mesh = comp.mesh().create("mesh1"); mesh.automatic(True); mesh.autoMeshSize(int(size_index)); return mesh

def add_study(jm, f0=2.0e9, f1=3.0e9, df=2.0e7):
    std = jm.study().create("std1"); st = std.create("freq", "Frequency")
    st.set("plist", f"range({f0:g}[Hz],{df:g}[Hz],{f1:g}[Hz])"); return std
