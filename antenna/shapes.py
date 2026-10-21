import json, math
from dataclasses import dataclass, asdict
from params import P, derived, dielectric_layers

LAYERS = {"TOP": 1, "INNER": 2, "BOTTOM": 3, "VIA": 10, "BOARD": 100, "FEP": 101, "LIVER": 102, "AIRPAD": 103, "BOARD_CORE": 104, "BOARD_UPPER": 105, "PORT": 201}

@dataclass(frozen=True)
class Poly:
    layer: str
    pts: tuple
    hole: bool = False
    tag: str = ""

@dataclass(frozen=True)
class Via:
    x: float
    y: float
    drill: float
    pad: float
    kind: str
    z0: float
    z1: float

def rect(layer, x0, y0, x1, y1, tag="", hole=False):
    return Poly(layer, ((x0, y0), (x1, y0), (x1, y1), (x0, y1)), hole, tag)

def circle(cx, cy, d, n):
    r = d / 2
    return tuple((cx + r * math.cos(2 * math.pi * k / n), cy + r * math.sin(2 * math.pi * k / n)) for k in range(n))

def trace(layer, xa, ya, xb, yb, w, tag=""):
    L = math.hypot(xb - xa, yb - ya); ux, uy = (xb - xa) / L, (yb - ya) / L
    nx, ny = -uy * w / 2, ux * w / 2
    return Poly(layer, ((xa + nx, ya + ny), (xb + nx, yb + ny), (xb - nx, yb - ny), (xa - nx, ya - ny)), False, tag)

def miter_fill(x4, ya, xb, yb, w):
    """Copper that turns the square-ended join of the straight arm (along +x, ending at x4) and the slanted trace from (x4, ya)
    to (xb, yb) into one sharp outer corner: the two outer edges extended to their intersection (Wen 2021 Fig. 4b draws it so)."""
    L = math.hypot(xb - x4, yb - ya); ux, uy = (xb - x4) / L, (yb - ya) / L
    sg = 1.0 if uy > 0 else -1.0                                  # turn towards +y: the outer side is -y, and the reverse
    rc = (x4 + sg * uy * w / 2, ya - sg * ux * w / 2)              # the slant's start corner on the outer side
    t = (-sg * w / 2 + sg * ux * w / 2) / uy                       # along the slant's outer edge back to the arm's outer edge
    return ((x4, ya), (x4, ya - sg * w / 2), (rc[0] + t * ux, ya - sg * w / 2), rc)

def build(p=P):
    d = derived(p); polys, vias = [], []
    zb, zt = d["z_bot"], d["z_top"]
    hw = p.W4 / 2
    # board outline (paddle + strip + wedge), FR4 brick
    outline = ((0, -p.paddle_w / 2), (p.L1, -p.paddle_w / 2), (p.L1, -hw), (d["x_wedge0"], -hw),
               (d["x_tip"], 0.0), (d["x_wedge0"], hw), (p.L1, hw), (p.L1, p.paddle_w / 2), (0, p.paddle_w / 2))
    # one brick for Wen's single FR4 block; three stacked bricks (lower prepreg, core, upper prepreg) for a layered stack
    for name in ("BOARD", "BOARD_CORE", "BOARD_UPPER")[:len(dielectric_layers(p))]:
        polys.append(Poly(name, outline))
    # feed: launch strip + microstrip pad (top), ground (bottom) with antipad, port
    polys.append(rect("TOP", 0, -p.W6 / 2, d["x_launch_end"], p.W6 / 2, "launch"))
    polys.append(rect("TOP", d["x_launch_end"], -p.W1 / 2, d["x_pad_end"], p.W1 / 2, "pad"))
    polys.append(rect("BOTTOM", 0, -p.paddle_w / 2, p.L1, p.paddle_w / 2, "ground"))
    polys.append(Poly("BOTTOM", circle(d["x_feed_via"], 0.0, p.D_antipad, 64), True, "antipad"))
    polys.append(rect("PORT", 0.0, -p.W6 / 2, 0.1, p.W6 / 2, "port1"))
    vias.append(Via(d["x_feed_via"], 0.0, p.d_feed, p.feed_inner_pad, "feed", zb, zt))
    polys.append(Poly("INNER", circle(d["x_feed_via"], 0.0, p.feed_inner_pad, 64), False, "feedpad"))
    # SICL: plates, inner strip, fence
    polys.append(rect("TOP", d["x_sicl0"], -p.plate_w / 2, d["x_sicl1"], p.plate_w / 2, "plate"))
    polys.append(rect("BOTTOM", d["x_sicl0"], -p.plate_w / 2, d["x_sicl1"], p.plate_w / 2, "plate"))
    polys.append(rect("INNER", d["x_feed_via"], -p.w_inner / 2, d["x_inner_end"], p.w_inner / 2, "inner"))
    n_f = int(math.floor((p.sicl_len - p.fence_pitch / 2) / p.fence_pitch))
    for k in range(n_f):
        x = d["x_sicl0"] + p.fence_pitch / 2 + k * p.fence_pitch
        for y in (-p.a / 2, p.a / 2):
            vias.append(Via(x, y, p.fence_drill, p.fence_drill, "fence", zb, zt))
    # radiator: straight arms, first partial slants, bifilar helix
    xs, x4, yr = d["x_sicl1"], d["x_sicl1"] + p.L4, d["y_row"]
    polys.append(rect("TOP", xs, -p.W5 / 2, x4, p.W5 / 2, "armA"))
    polys.append(rect("BOTTOM", xs, -p.W5 / 2, x4, p.W5 / 2, "armB"))
    x0 = d["x_helix0"]
    polys.append(trace("TOP", x4, 0.0, x0, +yr, p.W5, "helix"))      # arm A first segment -> (+row, k=0)
    polys.append(trace("BOTTOM", x4, 0.0, x0, -yr, p.W5, "helixB0")) # arm B first segment -> (-row, k=0)
    if p.arm_miter_join:  # sharp outer corner at the bend; before 2026-10-21 the two square ends met with a notch
        polys.append(Poly("TOP", miter_fill(x4, 0.0, x0, +yr, p.W5), False, "miter"))
        polys.append(Poly("BOTTOM", miter_fill(x4, 0.0, x0, -yr, p.W5), False, "miter"))
    for k in range(p.n_helix_steps + 1):
        x = x0 + k * p.L5
        for y in (-yr, yr):
            vias.append(Via(x, y, p.helix_drill, p.helix_pad, "helix", zb, zt))
            for lay in ("TOP", "BOTTOM"):
                polys.append(Poly(lay, circle(x, y, p.helix_pad, 32), False, "hpad"))
    for k in range(p.n_helix_steps):
        x = x0 + k * p.L5
        polys.append(trace("TOP", x, -yr, x + p.L5, +yr, p.W5, "helix"))     # top: -row -> +row
        polys.append(trace("BOTTOM", x, +yr, x + p.L5, -yr, p.W5, "helixB"))  # bottom: +row -> -row
    if p.helix_tip_bar:  # Fig. 4b: one more bar per layer from the last pad, ending free (no via)
        x = x0 + p.n_helix_steps * p.L5
        polys.append(trace("TOP", x, -yr, x + p.L5, +yr, p.W5, "helix"))
        polys.append(trace("BOTTOM", x, +yr, x + p.L5, -yr, p.W5, "helixB"))
    # housing and tissue boxes (bricks)
    t = p.fep_t
    polys.append(rect("FEP", d["x_sicl0"], -hw - t, d["x_tip"] + t, hw + t, "fep"))
    # air brick behind the feed: gds2palace sizes its simulation box from the drawn layers, and a lumped port must sit inside the
    # model, not on its outer wall (Ansys HFSS Port Basics); the COMSOL model has the same 5 mm of air
    polys.append(rect("AIRPAD", -p.air_margin, -hw, 0.0, hw, "airpad"))
    m = p.liver_margin
    polys.append(rect("LIVER", d["x_liver0"], -hw - m, d["x_tip"] + m, hw + m, "liver"))
    return polys, vias

def solver_variant(polys, vias, p=P, n_gon=8):
    d = derived(p)
    out_v = [v for v in vias if v.kind != "fence"]
    out_p = list(polys)
    for y in (-p.a / 2, p.a / 2):
        out_p.append(rect("VIA", d["x_sicl0"], y - p.fence_drill / 2, d["x_sicl1"], y + p.fence_drill / 2, "wall"))
    for v in out_v:
        out_p.append(Poly("VIA", circle(v.x, v.y, v.drill, n_gon), False, v.kind))
    return out_p, out_v

def to_json(polys, vias, path):
    with open(path, "w") as f:
        json.dump({"polys": [asdict(q) for q in polys], "vias": [asdict(v) for v in vias]}, f, indent=1)
