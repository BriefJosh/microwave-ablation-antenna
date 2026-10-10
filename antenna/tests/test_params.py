import math
import params
from params import P, derived

D = derived(P)

def test_dielectric_stack_is_paper_stack():
    # Wen 2021 §II.A: FR4 0.2 / bonding 0.265 / FR4 0.2 between the coppers
    assert math.isclose(D["z_top"] - D["z_bot"], 0.665, abs_tol=1e-9)
    assert math.isclose(D["z_top"] - D["z_inner"], 0.2, abs_tol=1e-9)

def test_sicl_is_54_mm_and_L3_reaches_the_wedge():
    assert math.isclose(D["x_sicl1"] - D["x_sicl0"], 54.0)
    assert math.isclose(D["x_wedge0"] - D["x_sicl0"], P.L3)

def test_inner_arm_is_L6_past_the_sicl():
    assert math.isclose(D["x_inner_end"] - D["x_sicl1"], P.L6)

def test_helix_fits_inside_inner_arm():
    assert D["x_helix0"] > D["x_sicl1"] + P.L4
    assert D["x_helix_end"] < D["x_inner_end"]

def test_text_reading_arm_length_matches_paper_49_4mm():
    # §II.B: "lengths of the two parallel arms ... are both set to 49.4 mm". The text's number is reproduced by 12 steps and no tip bar.
    import dataclasses
    t = derived(dataclasses.replace(P, n_helix_steps=12, helix_tip_bar=False))
    assert abs(t["arm_len"] - 49.4) / 49.4 < 0.02

def test_baseline_follows_fig_4b_not_the_text_arm_length():
    # Fig. 4(b): 14 pads per row and 14 bars per layer, the last bar free. That geometry has about 56.1 mm of arm by the same formula, 14% more
    # than the text's 49.4 mm. The figure geometry is the one whose COMSOL dip lands on 2.45 GHz (results/comsol_diagnosis_2026-10-11.md).
    assert P.n_helix_steps == 13 and P.helix_tip_bar is True
    assert abs(D["arm_len"] - 56.1) < 0.2

def test_trace_angle_close_to_theta():
    # Table II theta = 77.173 deg; we space vias by L5 exactly, so the angle is derived
    assert abs(D["trace_angle_deg"] - P.theta_deg) < 0.5

def test_14_vias_per_row():
    # Fig. 4(b): 14 pads per row on the top layer and 14 dots per row on the inner layer (13 intervals of L5)
    assert D["n_vias_per_row"] == 14

def test_microstrip_impedance_near_23_66_ohm():
    # §II.B: 12.5 mm microstrip, Z0 = 23.66 ohm. Hammerstad closed form, zero-thickness strip.
    h = D["z_top"] - D["z_bot"]; u = P.W1 / h; er = P.eps_fr4
    eeff = (er + 1) / 2 + (er - 1) / 2 / math.sqrt(1 + 12 / u)
    z0 = 120 * math.pi / (math.sqrt(eeff) * (u + 1.393 + 0.667 * math.log(u + 1.444)))
    assert abs(z0 - 23.66) / 23.66 < 0.05

def test_every_field_has_a_source_tag():
    for name in P.__dataclass_fields__:
        assert name in params.SOURCES, name


def test_full_stack_has_real_copper_thicknesses_and_paper_height():
    # Wen 2021 S II.A: copper 0.035 / FR4 0.2 / inner Cu 0.0175 / bonding 0.265 / FR4 0.2 / copper 0.035 mm
    F = params.derived_full(P)
    assert math.isclose(P.t_cu_outer, 0.035) and math.isclose(P.t_cu_inner, 0.0175)
    assert math.isclose(F["z_bot_cu0"], -0.035) and math.isclose(F["z_bot_cu1"], 0.0)
    assert math.isclose(F["z_inner_cu0"], 0.2) and math.isclose(F["z_inner_cu1"], 0.2175)
    assert math.isclose(F["z_top_cu0"], 0.6825) and math.isclose(F["z_top_cu1"], 0.7175)
    # between the plates: 0.2 + 0.0175 + 0.265 + 0.2 = 0.6825 mm, close to Table I b = 0.7 mm
    assert abs(F["z_top_cu0"] - F["z_bot_cu1"] - 0.7) / 0.7 < 0.03

def test_full_via_barrels_span_both_outer_coppers():
    F = params.derived_full(P)
    assert math.isclose(F["via_z0"], F["z_bot_cu0"]) and math.isclose(F["via_z1"], F["z_top_cu1"])
