"""Full-fidelity COMSOL variant: copper traces with their real thickness (35 um outer, 17.5 um inner) as solid bodies, the SICL
fence as 90 real via cylinders (and the feed and helix vias as real cylinders). Copper bodies are PEC (no field inside, boundary
condition on every face), so only the GEOMETRY differs from the idealised model; set sigma_cu to add surface-impedance loss.
Same domains, materials, port and mesh controls as build_comsol; selections: csel_cu_all."""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, ".."))
import jpype
from params import P, derived, derived_full
import shapes, stackup
import build_comsol as B


def _circle(wg, tag, x, y, d):
    c = wg.create(tag, "Circle"); c.set("r", d / 2); c.set("pos", [x, y]); return c

def _extrude(geom, tag, wp_tag, z0, dz, contribute=None):
    e = geom.create(tag, "Extrude"); e.selection("input").set([wp_tag]); e.set("distance", [dz])
    if contribute: e.set("contributeto", contribute)
    return e

def build_geometry_full(jm, p=P, liver_margin=None, omit=()):
    """omit: names among {'BOTTOM','INNER','TOP','vias'} left out (bisecting the lumped-port compile check, 2026-10-11)."""
    d = derived(p); F = derived_full(p)
    zb, zt = F["z_bot_cu0"], F["z_top_cu1"]; zp0, zp1 = F["z_bot_cu1"], F["z_top_cu0"]   # board dielectric spans zp0..zp1
    m = p.liver_margin if liver_margin is None else liver_margin; big = m + 5
    polys, vias = shapes.build(p)                         # fab truth: real fence vias, real drills
    comp = jm.component().create("comp1", True)
    geom = comp.geom().create("geom1", 3); geom.lengthUnit("mm")
    for nm in ("cu_all", "port", "dom_air", "dom_liver", "dom_fep", "dom_board"):
        geom.selection().create(f"csel_{nm}", "CumulativeSelection")
    hw = p.W4 / 2
    def blk(tag, x0, y0, z0, x1, y1, z1, contribute):
        b = geom.create(tag, "Block"); b.set("pos", [x0, y0, z0]); b.set("size", [x1 - x0, y1 - y0, z1 - z0]); b.set("contributeto", contribute)
    blk("air", -p.air_margin, -(hw + m), zb - big, d["x_tip"] + m, hw + m, zt + big, "csel_dom_air")
    blk("liver", d["x_liver0"], -(hw + m), zb - m, d["x_tip"] + m, hw + m, zt + m, "csel_dom_liver")
    blk("fep", d["x_sicl0"], -(hw + p.fep_t), zb - p.fep_t, d["x_tip"] + p.fep_t, hw + p.fep_t, zt + p.fep_t, "csel_dom_fep")
    wb = geom.create("wp_board", "WorkPlane"); wb.set("quickplane", "xy"); wb.set("quickz", float(zp0)); wb.set("unite", True)
    bpoly = next(q for q in polys if q.layer == "BOARD"); B._poly_feature(wb.geom(), "b", bpoly.pts)
    _extrude(geom, "board", "wp_board", zp0, zp1 - zp0, "csel_dom_board")
    # copper bodies: one work plane + extrusion per layer (holes subtracted in 2D)
    names = []
    for lay, z0, z1 in (("BOTTOM", F["z_bot_cu0"], F["z_bot_cu1"]), ("INNER", F["z_inner_cu0"], F["z_inner_cu1"]), ("TOP", F["z_top_cu0"], F["z_top_cu1"])):
        if lay in omit: continue
        add, holes = B._layer_polys(polys, lay)
        B._workplane(geom, f"wp_{lay.lower()}", z0, add, holes, None)
        _extrude(geom, f"cu_{lay.lower()}", f"wp_{lay.lower()}", z0, z1 - z0); names.append(f"cu_{lay.lower()}")
    # via barrels: real circles through the whole stack
    if "vias" not in omit:
        wv = geom.create("wp_via", "WorkPlane"); wv.set("quickplane", "xy"); wv.set("quickz", float(F["via_z0"])); wv.set("unite", True)
        for i, v in enumerate(vias): _circle(wv.geom(), f"v{i}", v.x, v.y, v.drill)
        _extrude(geom, "cu_vias", "wp_via", F["via_z0"], F["via_z1"] - F["via_z0"]); names.append("cu_vias")
    have_cu = bool(names)
    if have_cu:
        u = geom.create("cu", "Union"); u.selection("input").set(names); u.set("intbnd", False); u.set("contributeto", "csel_cu_all")
    # port face on the x = 0 wall between the plates
    wpp = geom.create("wp_port", "WorkPlane"); wpp.set("planetype", "quick"); wpp.set("quickplane", "yz"); wpp.set("quickx", 0.0); wpp.set("unite", True)
    r = wpp.geom().create("r", "Rectangle"); r.set("pos", [-p.W6 / 2, float(zp0)]); r.set("size", [p.W6, float(zp1 - zp0)]); wpp.set("contributeto", "csel_port")
    # booleans: tools stay until their last use as an input
    def dif(tag, inp, tools):
        x = geom.create(tag, "Difference"); x.selection("input").set([inp]); x.selection("input2").set(tools); x.set("keepsubtract", True)
    cu = ["cu"] if have_cu else []
    dif("dif_air", "air", ["liver", "fep", "board"] + cu); dif("dif_liver", "liver", ["fep", "board"] + cu)
    dif("dif_fep", "fep", ["board"] + cu)
    if cu: dif("dif_board", "board", cu)
    return comp, geom
