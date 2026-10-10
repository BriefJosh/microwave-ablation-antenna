import math
from params import P, derived
import shapes

D = derived(P)
POLYS, VIAS = shapes.build()

def by(layer): return [q for q in POLYS if q.layer == layer and not q.hole]

def test_helix_vias_alternate_rows_every_L5():
    hv = sorted([v for v in VIAS if v.kind == "helix"], key=lambda v: (v.y, v.x))
    rows = {}
    for v in hv: rows.setdefault(round(v.y, 6), []).append(v.x)
    assert set(rows) == {round(-D["y_row"], 6), round(D["y_row"], 6)}
    for xs in rows.values():
        assert len(xs) == D["n_vias_per_row"]
        steps = [b - a for a, b in zip(xs, xs[1:])]
        assert all(math.isclose(s, P.L5, abs_tol=1e-9) for s in steps)

def test_top_layer_has_15_slanted_traces():
    # first partial slant + 13 full bars between via pads + the free tip bar (Fig. 4b: 14 full bars)
    tops = [q for q in by("TOP") if q.tag == "helix"]
    assert len(tops) == 15

def test_bottom_has_antipad_hole_at_feed_via():
    holes = [q for q in POLYS if q.layer == "BOTTOM" and q.hole]
    assert len(holes) == 1
    xs = [x for x, _ in holes[0].pts]
    assert math.isclose((max(xs) + min(xs)) / 2, D["x_feed_via"], abs_tol=1e-6)
    assert math.isclose(max(xs) - min(xs), P.D_antipad, rel_tol=0.01)

def test_inner_strip_runs_from_feed_via_to_L6():
    xs = [x for q in by("INNER") for x, _ in q.pts]
    assert min(xs) <= D["x_feed_via"] and math.isclose(max(xs), D["x_inner_end"])

def test_fence_vias_two_rows_at_W2_over_sicl():
    fv = [v for v in VIAS if v.kind == "fence"]
    assert {round(v.y, 6) for v in fv} == {round(-P.a / 2, 6), round(P.a / 2, 6)}
    assert all(D["x_sicl0"] < v.x < D["x_sicl1"] for v in fv)

def test_solver_variant_replaces_fence_by_two_walls():
    pp, vv = shapes.solver_variant(POLYS, VIAS)
    assert not [v for v in vv if v.kind == "fence"]
    walls = [q for q in pp if q.layer == "VIA" and q.tag == "wall"]
    assert len(walls) == 2

def test_port_sits_at_x0_across_launch_strip():
    port = [q for q in POLYS if q.layer == "PORT"]
    assert len(port) == 1
    ys = [y for _, y in port[0].pts]; xs = [x for x, _ in port[0].pts]
    assert math.isclose(max(ys) - min(ys), P.W6) and math.isclose(min(xs), 0.0)


def test_air_pad_extends_the_simulation_box_behind_the_feed():
    # a lumped port must sit inside the model (Ansys HFSS Port Basics, slide 6/11): gds2palace sizes its box from the drawn
    # layers, so an AIR brick drawn at x in [-air_margin, 0] puts 5 mm of air behind the port, as in the COMSOL model
    pad = [q for q in POLYS if q.layer == "AIRPAD"]
    assert len(pad) == 1
    xs = [x for x, _ in pad[0].pts]
    assert math.isclose(min(xs), -P.air_margin) and math.isclose(max(xs), 0.0)

def test_helix_tip_bar_adds_one_dangling_bar_per_layer_and_no_via():
    # Fig. 4b: 14 pads per row, 14 full bars per layer, the last bar ends free beyond the last pad (13 steps + tip bar)
    import dataclasses
    p = dataclasses.replace(P, n_helix_steps=13, helix_tip_bar=True)
    polys, vias = shapes.build(p); d = derived(p)
    tops = [q for q in polys if q.layer == "TOP" and q.tag == "helix" and not q.hole]
    bots = [q for q in polys if q.layer == "BOTTOM" and q.tag == "helixB" and not q.hole]
    assert len(tops) == 15 and len(bots) == 14   # top: partial + 13 steps + tip bar; bottom: 13 steps + tip bar (its partial is tagged helixB0)
    assert len([v for v in vias if v.kind == "helix"]) == 2 * 14                 # 14 vias per row, none under the tip bar
    x_end = d["x_helix0"] + 14 * p.L5
    assert max(x for q in tops for x, _ in q.pts) > x_end - 1e-6 and not any(abs(v.x - x_end) < 1e-6 for v in vias)

def test_text_variant_has_no_tip_bar():
    import dataclasses
    polys, _ = shapes.build(dataclasses.replace(P, n_helix_steps=12, helix_tip_bar=False))
    assert len([q for q in polys if q.layer == "TOP" and q.tag == "helix"]) == 13
