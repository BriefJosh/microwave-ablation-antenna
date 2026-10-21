"""JLCPCB via rules and the geometry checks run before a solve.
Terms (JLCPCB's): via hole size = the drilled hole (the solver's pillar, params.helix_drill); via diameter = the copper pad edge to
edge (params.helix_pad); annular ring = (via diameter - hole) / 2; pitch = centre to centre; hole-to-hole spacing = edge to edge.
Rules quoted from jlcpcb.com/capabilities/pcb-capabilities (read 2026-10-20): "0.1mm or 0.15mm hole size with any size via diameter,
and 0.2mm or 0.25mm hole size with via diameter less than 0.45mm, will cost more"; "Via Hole-to-Hole Spacing: 0.2mm"."""
import math
from params import derived

TOL = 1e-6
MIN_HOLE_TO_HOLE = 0.2

def jlc_via_surcharge(hole, via_diameter):
    if hole < 0.15 + TOL:
        return True
    if hole < 0.25 + TOL:
        return via_diameter < 0.45 - TOL
    return False

def board_half_width_at(x, p):
    """Half-width of the board outline at x (mm): paddle, strip, then the wedge tapering to the tip."""
    d = derived(p)
    if x < 0 or x > d["x_tip"]:
        return 0.0
    if x < p.L1:
        return p.paddle_w / 2
    if x <= d["x_wedge0"]:
        return p.W4 / 2
    return p.W4 / 2 * (d["x_tip"] - x) / (d["x_tip"] - d["x_wedge0"])

def presolve_problems(p):
    """Empty list = the helix vias are drawable: hole smaller than the via diameter, every pad wholly on the board, and the
    hole-to-hole spacing along a row at least JLCPCB's 0.2 mm."""
    import shapes
    _, vias = shapes.build(p)
    out = []
    if p.helix_drill >= p.helix_pad - TOL:
        out.append(f"helix via hole {p.helix_drill} mm is not smaller than the via diameter {p.helix_pad} mm")
    if p.L5 - p.helix_drill < MIN_HOLE_TO_HOLE - TOL:
        out.append(f"helix hole-to-hole spacing {p.L5 - p.helix_drill:.3f} mm < {MIN_HOLE_TO_HOLE} mm")
    r = p.helix_pad / 2
    for v in (v for v in vias if v.kind == "helix"):
        for k in range(64):
            a = 2 * math.pi * k / 64
            x, y = v.x + r * math.cos(a), v.y + r * math.sin(a)
            if abs(y) > board_half_width_at(x, p) + TOL:
                out.append(f"helix pad at x={v.x:.3f}, y={v.y:.3f} reaches outside the board (|y| {abs(y):.3f} > {board_half_width_at(x, p):.3f} mm)")
                break
    return out
