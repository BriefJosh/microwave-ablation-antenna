"""Needs a COMSOL licence and ~1 min for the JVM: run with GATE_COMSOL=1. Checks that the geometry COMSOL builds from
params/shapes has the same copper areas as the reference GDS (gate: each layer within 1%)."""
import os, sys, pytest
import gds_ref, shapes

pytestmark = pytest.mark.skipif(os.environ.get("GATE_COMSOL") != "1", reason="set GATE_COMSOL=1 (needs COMSOL)")
HERE = os.path.dirname(os.path.abspath(__file__))
REF = os.path.join(HERE, "..", "results", "reference_solver.gds")

@pytest.fixture(scope="module")
def built():
    sys.path.insert(0, os.path.join(HERE, "..", "comsol"))
    import mph, build_comsol
    client = mph.start(cores=2)
    m, jm = build_comsol.new_model(client, "wen_gate_geom_test")
    comp, geom = build_comsol.build_geometry(jm); geom.run()
    yield comp, geom
    client.remove(m)

def _area(geom, tag, dim):
    ms = geom.measure(); ms.selection().init(dim); ms.selection().named(tag); return ms.getVolume()

@pytest.mark.parametrize("name,layer", [("cu_top", "TOP"), ("cu_inner", "INNER"), ("cu_bottom", "BOTTOM")])
def test_copper_area_matches_reference(built, name, layer):
    _, geom = built
    ref_mm2 = gds_ref.region(REF, shapes.LAYERS[layer]).area() * (gds_ref.DBU_UM / 1000) ** 2
    got = _area(geom, f"csel_{name}", 2)
    assert abs(got - ref_mm2) / ref_mm2 < 0.01, (name, got, ref_mm2)

def test_via_solid_volume_matches_reference(built):
    _, geom = built
    ref = gds_ref.region(REF, shapes.LAYERS["VIA"]).area() * (gds_ref.DBU_UM / 1000) ** 2 * 0.665
    got = _area(geom, "csel_cu_via", 3)
    assert abs(got - ref) / ref < 0.01, (got, ref)

def test_port_face_is_W6_by_board_thickness(built):
    from params import P, derived
    _, geom = built
    assert abs(_area(geom, "csel_port", 2) - P.W6 * derived(P)["z_top"]) < 1e-6


def test_study_compiles_on_a_minimal_mesh():
    """COMSOL's equation compiler rejects ports it considers badly placed (adjacent to absorbing features; not between two
    conductive boundaries). The only reliable test is to compile and solve once on the coarsest mesh (seconds, under 1 GB)."""
    import numpy as np
    sys.path.insert(0, os.path.join(HERE, "..", "comsol"))
    import mph, build_comsol
    client = mph.start(cores=2)
    m, jm = build_comsol.new_model(client, "wen_gate_compile_test")
    try:
        comp, geom = build_comsol.build_geometry(jm); geom.run()
        build_comsol.add_physics(jm, comp); mesh = build_comsol.add_mesh(comp, 9)
        build_comsol.add_study(jm, 2.45e9, 2.45e9, 1e7); mesh.run(); jm.study("std1").run()
        s11 = np.atleast_1d(m.evaluate("emw.S11")).ravel()
        assert np.all(np.isfinite(s11)) and abs(s11[0]) <= 1.05, s11
    finally:
        client.remove(m)
