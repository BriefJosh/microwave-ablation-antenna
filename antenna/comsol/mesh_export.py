"""Mesh the Wen 2021 gate geometry at Physics-Controlled indices without solving; export sizes and planar cuts of the mesh.
usage: python mesh_export.py <out_dir> [indices, default 9,8,7,6,5] [f0,f1,df GHz, default 2.3,2.6,0.025: the record's grid; the mesh follows the top frequency]
Never saves a model. The physics-controlled size depends on the study's highest frequency, so the study is added (not run).
A cut is the set of polygons where the plane crosses the tetrahedra (triangles or quads), so it works away from boundaries too."""
import json, os, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, ".."))

RECORD = {9: 163205, 8: 180447, 7: 221979, 6: 267299, 5: 361970}   # element counts of the solved sweeps (index: elements)
AX = {"x": 0, "y": 1, "z": 2}

def check_count(idx, n):
    """Within 0.5 % of the record: COMSOL re-meshing the same geometry in one session differs by up to about 0.2 %."""
    if idx in RECORD and abs(n / RECORD[idx] - 1) > 0.005:
        raise ValueError(f"index {idx}: {n} elements, record says {RECORD[idx]}")

def crop(pts, tris, window):
    x0, x1, y0, y1 = window
    inside = (pts[:, 0] >= x0) & (pts[:, 0] <= x1) & (pts[:, 1] >= y0) & (pts[:, 1] <= y1)
    keep = tris[inside[tris].all(axis=1)]
    used = np.unique(keep); remap = -np.ones(len(pts), int); remap[used] = np.arange(len(used))
    return pts[used], remap[keep]

def slice_tets(pts, tets, c, axis=2):
    """Polygons (in the two remaining coordinates) where the plane coord[axis] = c cuts each tetrahedron."""
    keep = [k for k in range(3) if k != axis]
    s = pts[:, axis] - c
    out = []
    S = s[tets]
    cand = np.where((S.min(axis=1) < 0) & (S.max(axis=1) > 0))[0]
    for e in cand:
        v = tets[e]; P = []
        for a in range(4):
            for b in range(a + 1, 4):
                sa, sb = s[v[a]], s[v[b]]
                if (sa < 0) != (sb < 0):
                    t = sa / (sa - sb); P.append(pts[v[a]] + t * (pts[v[b]] - pts[v[a]]))
        P = np.array(P)[:, keep]
        m = P.mean(axis=0); P = P[np.argsort(np.arctan2(P[:, 1] - m[1], P[:, 0] - m[0]))]   # convex: order by angle
        out.append(P)
    return out

def crop_polys(polys, window):
    x0, x1, y0, y1 = window
    return [P for P in polys if P[:, 0].min() >= x0 and P[:, 0].max() <= x1 and P[:, 1].min() >= y0 and P[:, 1].max() <= y1]

def _sizes(comp):
    """The Size node(s) COMSOL generated for the automatic mesh, as strings (the measurement the slides quote)."""
    m = comp.mesh("mesh1"); out = {}
    for tag in m.feature().tags():
        f = m.feature(tag)
        if str(f.getType()) == "Size":
            d = {}
            for p in f.properties():
                if str(p) in ("hauto", "hmax", "hmin", "hgrad", "hcurve", "hnarrow", "custom", "table"):
                    try: d[str(p)] = str(f.getString(p))
                    except Exception: pass
            try: d["selection"] = [int(i) for i in f.selection().entities()]
            except Exception: pass
            out[str(tag)] = d
    return out

def cuts_for(p):
    from params import derived
    d = derived(p); zm = (d["z_inner"] + d["z_top"]) / 2; hw = p.W4 / 2
    return [dict(name="cross-section through the SICL, liver around it", axis="x", at=p.L1 + p.liver_start_from_paddle + 8.0,
                 window=[-hw - 3.0, hw + 3.0, d["z_top"] / 2 - 2.6, d["z_top"] / 2 + 2.6]),
            dict(name="top view, mid-dielectric, around the feed and first fence vias", axis="z", at=zm,
                 window=[p.L1 - 2.0, p.L1 + 6.0, -hw - 1.0, hw + 1.0])]

def main(out_dir, idxs=(9, 8, 7, 6, 5), grid=(2.3, 2.6, 0.025)):
    import mph, build_comsol as B, params
    c = mph.start(cores=int(os.environ.get("GATE_COMSOL_CORES", "6")))
    p = params.P; bad = []
    for idx in idxs:
        m, jm = B.new_model(c, f"meshonly_i{idx}")
        try:
            comp, geom = B.build_geometry(jm, p); geom.run(); B.add_physics(jm, comp, p)
            B.add_study(jm, grid[0] * 1e9, grid[1] * 1e9, grid[2] * 1e9)
            mesh = B.add_mesh(comp, idx); assert mesh.isAutomatic(); mesh.run()
            n = int(mesh.getNumElem())
            mm = comp.mesh("mesh1")
            pts = np.array(mm.getVertex(), float).T
            tets = np.array(mm.getElem("tet"), int).T
            cuts = []
            for cu in cuts_for(p):
                polys = crop_polys(slice_tets(pts, tets, cu["at"], AX[cu["axis"]]), cu["window"])
                cuts.append(dict(cu, polys=[np.round(P, 4).tolist() for P in polys]))
            d = dict(index=idx, n_elem=n, n_tet=int(len(tets)), record=RECORD.get(idx), grid_GHz=list(grid),
                     size=_sizes(comp), cuts=cuts, model="Wen 2021 stack (params.P), PEC copper, wall fence, liver margin 30 mm")
            json.dump(d, open(os.path.join(out_dir, f"mesh_i{idx}.json"), "w"))
            print(idx, n, "record", RECORD.get(idx), [len(c_["polys"]) for c_ in cuts], "cut polygons", flush=True)
            try: check_count(idx, n)
            except ValueError as e: bad.append(str(e))
        finally:
            c.remove(m)                                            # never saved
    if bad:
        raise SystemExit("element counts differ from the record:\n" + "\n".join(bad))

if __name__ == "__main__":
    a = sys.argv[1:]
    main(a[0], tuple(int(x) for x in a[1].split(",")) if len(a) > 1 else (9, 8, 7, 6, 5),
         tuple(float(x) for x in a[2].split(",")) if len(a) > 2 else (2.3, 2.6, 0.025))
