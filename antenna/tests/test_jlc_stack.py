import dataclasses, math
from params import P, JLC, derived, dielectric_layers

def test_wen_stack_is_one_fr4_block():
    L = dielectric_layers(P)
    assert len(L) == 1 and math.isclose(L[0]["z0"], 0.0) and math.isclose(L[0]["z1"], 0.665, abs_tol=1e-9)
    assert L[0]["eps"] == 4.8 and L[0]["tand"] == 0.02

def test_jlc_stack_is_the_7628_template():
    # JLC04081H-7628 as shown on JLCPCB's order form 2026-10-05: prepreg 0.2104 / core 0.25 / prepreg 0.2104 mm; copper 0.035 / 0.0152 / 0.0152 / 0.035
    d = derived(JLC)
    assert math.isclose(d["z_inner"], 0.4604, abs_tol=1e-9) and math.isclose(d["z_top"], 0.6708, abs_tol=1e-9)
    assert JLC.t_cu_outer == 0.035 and JLC.t_cu_inner == 0.0152

def test_jlc_has_three_dielectric_layers_with_vendor_permittivities():
    L = dielectric_layers(JLC)
    assert [round(l["eps"], 2) for l in L] == [4.4, 4.23, 4.4]       # JLCPCB-stated NP-155F: prepreg 4.4, core 4.23
    assert [l["name"] for l in L] == ["PREPREG_LOWER", "CORE", "PREPREG_UPPER"]
    assert math.isclose(L[0]["z1"], L[1]["z0"]) and math.isclose(L[1]["z1"], L[2]["z0"])
    assert math.isclose(L[0]["z1"], 0.2104, abs_tol=1e-9) and math.isclose(L[1]["z1"], 0.4604, abs_tol=1e-9)
    assert all(l["tand"] == 0.014 for l in L)                           # secondary-source estimate, flagged assumption

def test_jlc_changes_only_the_stack():
    stack = {"h_top", "h_bond", "h_bot", "t_cu_inner", "eps_layers", "tand_layers"}
    for f in dataclasses.fields(P):
        if f.name in stack: continue
        assert getattr(JLC, f.name) == getattr(P, f.name), f.name


# ---- three-layer board in the geometry, stackup XML and GDS (2026-10-12) ----
import os, tempfile, re
import shapes, stackup, gds_ref

def test_wen_board_is_one_brick_and_jlc_board_is_three_with_the_same_outline():
    wen = [q for q in shapes.build(P)[0] if q.layer.startswith("BOARD")]
    assert [q.layer for q in wen] == ["BOARD"]
    jlc = [q for q in shapes.build(JLC)[0] if q.layer.startswith("BOARD")]
    assert [q.layer for q in jlc] == ["BOARD", "BOARD_CORE", "BOARD_UPPER"]
    assert jlc[0].pts == jlc[1].pts == jlc[2].pts and jlc[0].pts == wen[0].pts
    assert shapes.LAYERS["BOARD_CORE"] == 104 and shapes.LAYERS["BOARD_UPPER"] == 105

def _xml(p):
    f = os.path.join(tempfile.mkdtemp(), "s.xml"); stackup.write(f, p); return open(f, encoding="utf-8").read()

def test_stackup_wen_keeps_the_single_fr4_layer():
    x = _xml(P)
    assert x.count('Type="dielectric"') == 4          # LIVER, FEP, AIRPAD and BOARD
    assert re.search(r'<Layer Name="BOARD" Type="dielectric" Zmin="0" Zmax="665" Material="FR4"', x)
    assert "BOARD_CORE" not in x

def test_stackup_jlc_has_three_board_layers_with_their_materials():
    x = _xml(JLC)
    lay = {m.group(1): (int(m.group(2)), int(m.group(3)), m.group(4)) for m in re.finditer(r'<Layer Name="(BOARD\w*)" Type="dielectric" Zmin="(-?\d+)" Zmax="(-?\d+)" Material="(\w+)"', x)}
    assert lay == {"BOARD": (0, 210, "DIEL_PREPREG_LOWER"), "BOARD_CORE": (210, 460, "DIEL_CORE"), "BOARD_UPPER": (460, 671, "DIEL_PREPREG_UPPER")}
    eps = {m.group(1): float(m.group(2)) for m in re.finditer(r'<Material Name="(DIEL_\w+)" Type="Dielectric" Permittivity="([\d.]+)"', x)}
    assert eps == {"DIEL_PREPREG_LOWER": 4.4, "DIEL_CORE": 4.23, "DIEL_PREPREG_UPPER": 4.4}
    assert re.search(r'<Layer Name="INNER" Type="sheet" Zmin="460" Zmax="460"', x) and re.search(r'<Layer Name="TOP" Type="sheet" Zmin="671" Zmax="671"', x)
    assert 'Material="FR4"' not in x

def test_gds_ref_writes_the_three_board_layers_for_jlc():
    import klayout.db as kdb
    polys, vias = shapes.build(JLC); path = os.path.join(tempfile.mkdtemp(), "j.gds"); gds_ref.write(polys, vias, path)
    areas = {l: gds_ref.region(path, l).area() for l in (100, 104, 105)}
    assert areas[100] > 0 and areas[100] == areas[104] == areas[105]

def test_solver_gds_builder_takes_the_extra_board_layers():
    import build_solver_gds
    assert {104, 105} <= set(build_solver_gds.TAKE) and build_solver_gds.TAKE[104] == "fab"
