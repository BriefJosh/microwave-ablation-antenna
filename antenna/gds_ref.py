import klayout.db as kdb
import shapes

DBU_UM = 0.001  # 1 nm database unit; GDS user unit is 1 um (gds2palace settings['unit'] = 1e-6)

def _poly(pts_mm):
    return kdb.Polygon([kdb.Point(round(x * 1000 / DBU_UM), round(y * 1000 / DBU_UM)) for x, y in pts_mm])

def write(polys, vias, path, circle_n=128, include_drill=True):
    ly = kdb.Layout(); ly.dbu = DBU_UM
    top = ly.create_cell("WEN2021")
    regions = {}
    for q in polys:
        r = regions.setdefault(q.layer, [kdb.Region(), kdb.Region()])
        r[1 if q.hole else 0].insert(_poly(q.pts))
    for name, (add, sub) in regions.items():
        li = ly.layer(shapes.LAYERS[name], 0)
        top.shapes(li).insert((add.merged() - sub.merged()).merged())
    if include_drill:
        li = ly.layer(shapes.LAYERS["VIA"], 0)
        reg = kdb.Region()
        for v in vias:
            reg.insert(_poly(shapes.circle(v.x, v.y, v.drill, circle_n)))
        top.shapes(li).insert(reg.merged())
    ly.write(path)

def region(path, layer):
    ly = kdb.Layout(); ly.read(path)
    li = ly.find_layer(layer, 0)
    if li is None: return kdb.Region()
    # copy the polygons out: a Region built straight from the iterator is empty once `ly` is freed
    return kdb.Region(ly.top_cell().begin_shapes_rec(li)).merged()
