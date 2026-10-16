"""COMSOL's own mesh plots of the Wen 2021 gate board (top view, white background, no axes) at Physics-Controlled indices.
usage: python mesh_plots.py <out_dir> [indices, default 9,8,7,6,5]
Mesh only on the record's grid (2.30 to 2.60 GHz; the mesh follows the top frequency), no solve, nothing saved.
Writes patch_i<idx>.png for every index, board_i6.png and helix_i6.png when 6 is in the list, and mesh_plots.json (windows, pixel sizes, counts)."""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, ".."))

GRID = (2.3e9, 2.6e9, 0.025e9)

def windows(p):
    """[x0, x1, y0, y1] in mm: the whole board, and the radiator end from the end of the inner strip's SICL to the tip."""
    from params import derived
    import shapes
    board = next(q for q in shapes.build(p)[0] if q.layer == "BOARD")
    d = derived(p); hw = max(abs(y) for _, y in board.pts) + 0.3                         # the feed paddle is the widest part
    yb = p.W4 / 2 + 0.3
    return {"board": [-0.5, d["x_tip"] + 0.5, -hw, hw],
            "helix": [d["x_helix0"] - 1.5, d["x_tip"] + 0.5, -yb, yb],                       # the radiator end
            "patch": [d["x_helix0"] - 0.3, d["x_helix0"] + 4.2, -yb, yb]}                    # the first helix turns, for B3

def pixels(window, width):
    x0, x1, y0, y1 = window
    return width, round(width * (y1 - y0) / (x1 - x0))

def _plot(jm, out, window, width):
    """Top-view orthographic image of the board's boundary mesh inside `window`."""
    x0, x1, y0, y1 = window
    wpx, hpx = pixels(window, width)
    v = jm.view("view1"); cam = v.camera()
    cam.set("projection", "orthographic")
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    cam.set("position", [str(cx), str(cy), "200"]); cam.set("target", [str(cx), str(cy), "0"]); cam.set("up", ["0", "1", "0"])
    cam.set("orthoscale", str(x1 - x0))
    v.set("showgrid", False) if "showgrid" in [str(p) for p in v.properties()] else None
    jm.result("pgm").run()                                   # apply the camera before the export renders
    ex = jm.result().export("img1")
    for k, val in (("size", "manualweb"), ("unit", "px"), ("lockratio", "off"), ("width", str(wpx)), ("height", str(hpx)),
                   ("zoomextents", "off"), ("options3d", "on"), ("title3d", "off"), ("legend3d", "off"), ("logo3d", "off"),
                   ("axisorientation", "off"), ("grid", "off"), ("background", "color"), ("customcolor", ["1", "1", "1"]), ("pngfilename", out)):
        ex.set(k, val)
    ex.run(); ex.run()                                       # COMSOL renders the view of the previous export on the first run
    return [wpx, hpx]

def main(out_dir, idxs=(9, 8, 7, 6, 5)):
    import mph, build_comsol as B, params
    c = mph.start(cores=int(os.environ.get("GATE_COMSOL_CORES", "6")))
    p = params.P; W = windows(p); info = dict(windows=W, grid_GHz=[g / 1e9 for g in GRID], model="Wen 2021 stack (params.P), wall fence, 8-gon vias", plots={})
    for idx in idxs:
        m, jm = B.new_model(c, f"meshplot_i{idx}")
        try:
            comp, geom = B.build_geometry(jm, p); geom.run(); B.add_physics(jm, comp, p)
            B.add_study(jm, *GRID)
            mesh = B.add_mesh(comp, idx); mesh.run(); n = int(mesh.getNumElem())
            board = B._ents(comp, "geom1_csel_dom_board_dom")
            ds = jm.result().dataset().create("dmesh", "Mesh"); ds.set("mesh", "mesh1")
            ds.selection().geom("geom1", 3); ds.selection().set(board)
            pg = jm.result().create("pgm", "PlotGroup3D"); pg.set("data", "dmesh"); pg.set("view", "view1")
            pg.set("titletype", "none"); pg.set("edges", False) if "edges" in [str(x) for x in pg.properties()] else None
            mp = pg.create("mp1", "Mesh"); mp.set("meshdomain", "surface"); mp.set("elemcolor", "gray"); mp.set("wireframecolor", "black")
            ex = jm.result().export().create("img1", "Image"); ex.set("sourceobject", "pgm")
            for k, val in (("options3d", "on"), ("title3d", "off"), ("legend3d", "off"), ("logo3d", "off"), ("axisorientation", "off"),
                           ("grid", "off"), ("background", "color"), ("customcolor", ["1", "1", "1"])):
                ex.set(k, val)
            info["plots"][idx] = {"n_elem": n, "patch": _plot(jm, os.path.join(out_dir, f"patch_i{idx}.png"), W["patch"], 900)}
            if idx == 6:
                info["plots"][idx]["board"] = _plot(jm, os.path.join(out_dir, "board_i6.png"), W["board"], 2400)
                info["plots"][idx]["helix"] = _plot(jm, os.path.join(out_dir, "helix_i6.png"), W["helix"], 2400)
            print(idx, n, "plotted", flush=True)
        finally:
            c.remove(m)                                            # never saved
    json.dump(info, open(os.path.join(out_dir, "mesh_plots.json"), "w"), indent=1)

if __name__ == "__main__":
    a = sys.argv[1:]
    main(a[0], tuple(int(x) for x in a[1].split(",")) if len(a) > 1 else (9, 8, 7, 6, 5))
