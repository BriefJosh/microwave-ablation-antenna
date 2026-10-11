"""'Real copper, real vias' variant that keeps COMSOL's Physics-Controlled Mesh: copper layers are zero-thickness faces carrying a
Transition Boundary Condition (sigma = 5.8e7 S/m, thickness 35 / 17.5 um, thick-layer option), the 90 fence vias (and the feed and
helix vias) are real circular cylinders with PEC walls. Needs COMSOL: GATE_COMSOL=1."""
import os, sys, pytest
import klayout.db as kdb
import gds_ref, shapes
from params import P

pytestmark = pytest.mark.skipif(os.environ.get("GATE_COMSOL") != "1", reason="set GATE_COMSOL=1 (needs COMSOL)")
HERE = os.path.dirname(os.path.abspath(__file__))
REF = os.path.join(HERE, "..", "results", "reference.gds")        # fab version: 128-gon via circles

@pytest.fixture(scope="module")
def built():
    sys.path.insert(0, os.path.join(HERE, "..", "comsol"))
    import mph, build_comsol
    client = mph.start(cores=4)
    m, jm = build_comsol.new_model(client, "wen_gate_tbc_test")
    comp, geom = build_comsol.build_geometry(jm, real_vias=True); geom.run()
    emw = build_comsol.add_physics(jm, comp, copper="tbc")
    yield m, jm, comp, geom, emw, build_comsol
    client.remove(m)

def _measure(geom, tag, dim):
    ms = geom.measure(); ms.selection().init(dim); ms.selection().named(tag); return ms.getVolume()

def test_via_cylinders_have_the_real_circle_volume(built):
    _, _, _, geom, _, _ = built
    ref = gds_ref.region(REF, shapes.LAYERS["VIA"]).area() * (gds_ref.DBU_UM / 1000) ** 2 * 0.665
    got = _measure(geom, "csel_cu_via", 3)
    assert abs(got - ref) / ref < 0.01, (got, ref)

def test_every_copper_face_carries_a_transition_boundary_condition(built):
    """A copper face piece without a TBC must lie inside a via cylinder (then it is not adjacent to any field domain)."""
    import numpy as np
    _, _, comp, geom, emw, bc = built
    faces = set()
    for n in ("top", "inner", "bottom"): faces |= set(bc._ents(comp, f"geom1_csel_cu_{n}_bnd"))
    tbc = set()
    for tag in emw.feature().tags():
        if str(tag).startswith("tbc"): tbc |= set(int(i) for i in emw.feature(tag).selection().entities())
    via = set(bc._ents(comp, "geom1_csel_cu_via_bnd"))
    assert tbc and tbc <= faces
    V = np.array(geom.getVertexCoord()); adj = geom.getAdj(2, 0)
    _, vias = shapes.build()
    for b in sorted(faces - via - tbc):
        X = V[:, [int(v) - 1 for v in adj[b]]]
        assert any(np.all(np.hypot(X[0] - v.x, X[1] - v.y) <= v.drill / 2 + 1e-6) for v in vias), ("copper piece without TBC outside every via", b)

def test_copper_material_has_the_real_conductivity_on_the_same_faces(built):
    _, _, comp, _, _, bc = built
    mt = comp.material("mat_cu")
    assert abs(float(str(mt.propertyGroup("def").getString("electricconductivity"))) - P.sigma_cu) < 1.0

def test_physics_controlled_mesh_builds_at_size_index_7(built):
    """The thin-solid version failed here ('Failed to respect edge element on geometry edge'); the TBC version must mesh."""
    m, jm, comp, geom, emw, bc = built
    mesh = bc.add_mesh(comp, 7); assert mesh.isAutomatic()
    mesh.run()
    assert int(mesh.getNumElem()) > 10_000

def test_study_compiles_and_gives_a_passive_s11_on_a_minimal_mesh(built):
    import numpy as np
    m, jm, comp, geom, emw, bc = built
    comp.mesh("mesh1").autoMeshSize(9); comp.mesh("mesh1").run()
    bc.add_study(jm, 2.45e9, 2.45e9, 1e7); jm.study("std1").run()
    s11 = np.atleast_1d(m.evaluate("emw.S11")).ravel()
    assert np.all(np.isfinite(s11)) and abs(s11[0]) <= 1.05, s11
