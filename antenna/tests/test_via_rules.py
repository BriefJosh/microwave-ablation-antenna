"""JLCPCB via-size surcharge rule and the pad-inside-board check run before every solve."""
from dataclasses import replace
import params
from analysis.via_rules import jlc_via_surcharge, board_half_width_at, presolve_problems

R = replace(params.JLC, L4=8.0, L3=72.5, L2=14.5)   # the retuned layout

def test_surcharge_rule():
    # JLCPCB: "0.2mm or 0.25mm hole size with via diameter less than 0.45mm, will cost more"; 0.1/0.15 mm holes always cost more
    assert jlc_via_surcharge(0.2, 0.40) is True
    assert jlc_via_surcharge(0.2, 0.449) is True
    assert jlc_via_surcharge(0.15, 0.60) is True
    for h, d in ((0.2, 0.45), (0.3, 0.45), (0.4, 0.50)):
        assert jlc_via_surcharge(h, d) is False

def test_half_width_on_strip_and_wedge():
    d = params.derived(R)
    assert board_half_width_at(50.0, R) == R.W4 / 2
    assert 0 < board_half_width_at((d["x_wedge0"] + d["x_tip"]) / 2, R) < R.W4 / 2
    assert board_half_width_at(d["x_tip"] + 1, R) == 0

def test_candidates_pass():
    for h, dia in ((0.2, 0.40), (0.2, 0.45), (0.3, 0.45), (0.4, 0.50)):
        assert presolve_problems(replace(R, helix_drill=h, helix_pad=dia)) == []

def test_pad_over_edge_flagged():
    assert any("outside" in s for s in presolve_problems(replace(R, helix_pad=0.8)))

def test_hole_not_smaller_than_pad_flagged():
    assert any("hole" in s for s in presolve_problems(replace(R, helix_drill=0.5, helix_pad=0.5)))

def test_pad_in_wedge_flagged():
    # L3 69.0 puts the wedge start (86.0 mm) before the last pads (87.2 mm), where the board is narrower than W4
    assert any("outside" in s for s in presolve_problems(replace(R, L3=69.0)))

def test_hole_to_hole_spacing_flagged():
    # 0.45 mm holes at 0.608 mm pitch leave 0.158 mm, under JLCPCB's 0.2 mm via hole-to-hole spacing
    assert any("spacing" in s for s in presolve_problems(replace(R, helix_drill=0.45, helix_pad=0.55)))
