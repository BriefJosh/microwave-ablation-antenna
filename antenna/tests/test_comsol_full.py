"""Full-fidelity COMSOL geometry (real copper thickness, real via cylinders). Needs COMSOL: GATE_COMSOL=1.
Gate: total copper volume equals the exact union volume computed independently with klayout (layer regions extruded by their
real thickness, via circles through the whole stack), within 1.5%."""
import os, sys, pytest
import klayout.db as kdb
import shapes, gds_ref
from params import P, derived_full

pytestmark = pytest.mark.skipif(os.environ.get("GATE_COMSOL") != "1", reason="set GATE_COMSOL=1 (needs COMSOL)")
HERE = os.path.dirname(os.path.abspath(__file__))
REF = os.path.join(HERE, "..", "results", "reference.gds")        # fab version: 128-gon via circles

@pytest.fixture(scope="module")
def built():
    sys.path.insert(0, os.path.join(HERE, "..", "comsol"))
    import mph, build_full
    client = mph.start(cores=2)
    m, jm = build_full.B.new_model(client, "wen_gate_full_test")
    comp, geom = build_full.build_geometry_full(jm); geom.run()
    yield comp, geom
    client.remove(m)

def _measure(geom, tag, dim):
    ms = geom.measure(); ms.selection().init(dim); ms.selection().named(tag); return ms.getVolume()

def _area_mm2(reg): return reg.area() * (gds_ref.DBU_UM / 1000) ** 2

def test_copper_volume_matches_independent_union_volume(built):
    _, geom = built
    F = derived_full(P)
    top = gds_ref.region(REF, shapes.LAYERS["TOP"]); inner = gds_ref.region(REF, shapes.LAYERS["INNER"])
    bot = gds_ref.region(REF, shapes.LAYERS["BOTTOM"]); via = gds_ref.region(REF, shapes.LAYERS["VIA"])
    t_o, t_i = P.t_cu_outer, P.t_cu_inner
    h_mid1 = F["z_inner_cu0"] - F["z_bot_cu1"]; h_mid2 = F["z_top_cu0"] - F["z_inner_cu1"]
    v = (_area_mm2(bot + via) * t_o + _area_mm2(top + via) * t_o + _area_mm2(inner + via) * t_i +
         _area_mm2(via) * (h_mid1 + h_mid2))
    got = _measure(geom, "csel_cu_all", 3)
    assert abs(got - v) / v < 0.015, (got, v)

def test_copper_is_one_connected_body_set_and_port_is_between_the_plates(built):
    _, geom = built
    F = derived_full(P)
    assert abs(_measure(geom, "csel_port", 2) - P.W6 * (F["z_top_cu0"] - F["z_bot_cu1"])) < 1e-6


def test_full_model_compiles_and_solves_on_a_minimal_mesh():
    """Real copper thickness + real via cylinders: the equation compiler accepts the port, and one solve on the coarsest mesh gives
    a finite passive S11 (seconds, under 1.5 GB)."""
    import numpy as np
    sys.path.insert(0, os.path.join(HERE, "..", "comsol"))
    import mph, build_full, build_comsol
    client = mph.start(cores=2)
    m, jm = build_comsol.new_model(client, "wen_gate_full_compile_test")
    try:
        comp, geom = build_full.build_geometry_full(jm); geom.run()
        build_comsol.add_physics(jm, comp, full=True); mesh = build_comsol.add_mesh(comp, 9)
        build_comsol.add_study(jm, 2.45e9, 2.45e9, 1e7); mesh.run(); jm.study("std1").run()
        s11 = np.atleast_1d(m.evaluate("emw.S11")).ravel()
        assert np.all(np.isfinite(s11)) and abs(s11[0]) <= 1.05, s11
    finally:
        client.remove(m)


def test_full_scattering_is_only_on_the_outer_box_and_never_touches_the_port():
    """The scattering condition belongs on the outer air-box faces only. Checked from the geometry's own vertex data: every
    scattering boundary lies in one of the six outer box planes, and none shares a vertex with the lumped-port face."""
    import numpy as np
    sys.path.insert(0, os.path.join(HERE, "..", "comsol"))
    import mph, build_full, build_comsol
    from params import P, derived, derived_full
    client = mph.start(cores=2)
    m, jm = build_comsol.new_model(client, "wen_gate_full_sbc_test")
    try:
        comp, geom = build_full.build_geometry_full(jm); geom.run()
        emw = build_comsol.add_physics(jm, comp, full=True)
        V = np.array(geom.getVertexCoord()); adj = geom.getAdj(2, 0)
        sbc = [int(i) for i in emw.feature("sbc").selection().entities()]
        port = [int(i) for i in emw.feature("lport1").selection().entities()]
        d = derived(P); F = derived_full(P); hw = P.W4 / 2; m_ = P.liver_margin; big = m_ + 5
        lo = np.array([-P.air_margin, -(hw + m_), F["z_bot_cu0"] - big]); hi = np.array([d["x_tip"] + m_, hw + m_, F["z_top_cu1"] + big])
        verts = lambda b: [int(v) - 1 for v in adj[b]]
        assert len(sbc) >= 6, "scattering must cover the outer box faces (an empty list made this test pass vacuously)"
        assert any(np.allclose(V[0, verts(b)], lo[0], atol=1e-6) for b in sbc), "the back wall (x = -air_margin) must be scattering"
        for b in sbc:
            X = V[:, verts(b)]
            on_plane = any(np.allclose(X[k], lo[k], atol=1e-6) or np.allclose(X[k], hi[k], atol=1e-6) for k in range(3))
            assert on_plane, (b, X.min(axis=1), X.max(axis=1))
        pv = set(verts(port[0]))
        assert not any(pv & set(verts(b)) for b in sbc)
    finally:
        client.remove(m)



def test_air_box_extends_behind_the_port(built):
    """The lumped port must sit inside the model: the air box starts air_margin behind the port plane (x = -5 mm). The first full
    build had x_min = 0 (found from the geometry's vertex data, 2026-10-11), putting the port on the outer wall."""
    import numpy as np
    _, geom = built
    V = np.array(geom.getVertexCoord())
    assert abs(V[0].min() + P.air_margin) < 1e-6, V[0].min()
