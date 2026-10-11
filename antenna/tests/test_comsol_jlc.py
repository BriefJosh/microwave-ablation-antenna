"""Needs a COMSOL licence: run with GATE_COMSOL=1. The layered JLCPCB board in COMSOL: three board domains with the right thicknesses
and materials, and the study compiles and solves on the coarsest mesh. One client for the module (mph.start works once per process)."""
import os, sys, pytest
import numpy as np
from params import JLC, derived, dielectric_layers
import shapes

pytestmark = pytest.mark.skipif(os.environ.get("GATE_COMSOL") != "1", reason="set GATE_COMSOL=1 (needs COMSOL)")
HERE = os.path.dirname(os.path.abspath(__file__))

@pytest.fixture(scope="module")
def jlc_model():
    sys.path.insert(0, os.path.join(HERE, "..", "comsol"))
    import mph, build_comsol
    client = mph.start(cores=2)
    m, jm = build_comsol.new_model(client, "wen_gate_jlc_test")
    comp, geom = build_comsol.build_geometry(jm, JLC); geom.run(); build_comsol.add_physics(jm, comp, JLC)
    yield build_comsol, m, jm, comp, geom
    client.remove(m)

def _vol(geom, tag, dim):
    ms = geom.measure(); ms.selection().init(dim); ms.selection().named(tag); return ms.getVolume()

def test_three_board_domains_with_the_layer_thicknesses(jlc_model):
    _, _, _, comp, geom = jlc_model
    v = [_vol(geom, f"csel_dom_board{i}", 3) for i in range(3)]
    t = [L["z1"] - L["z0"] for L in dielectric_layers(JLC)]; zt = derived(JLC)["z_top"]
    outline = shapes.build(JLC)[0][0]; pts = np.array(outline.pts)
    area = 0.5 * abs(np.dot(pts[:, 0], np.roll(pts[:, 1], -1)) - np.dot(pts[:, 1], np.roll(pts[:, 0], -1)))
    via = _vol(geom, "csel_cu_via", 3)
    assert abs(sum(v) + via - area * zt) / (area * zt) < 0.01, (v, via, area * zt)       # the board blocks plus the via solids fill the outline
    for vi, ti in zip(v, t): assert abs(vi / sum(v) - ti / zt) < 0.01, (v, t)            # equal via cross-section in every layer keeps the proportions

def test_each_board_domain_has_its_own_material(jlc_model):
    _, _, _, comp, _ = jlc_model
    eps = [float(str(comp.material(f"mat_diel{i}").propertyGroup("def").getString("relpermittivity"))) for i in range(3)]
    assert eps == [4.4, 4.23, 4.4], eps

def test_study_compiles_and_solves_on_a_minimal_mesh(jlc_model):
    build_comsol, m, jm, comp, _ = jlc_model
    mesh = build_comsol.add_mesh(comp, 9); build_comsol.add_study(jm, 2.45e9, 2.45e9, 1e7); mesh.run(); jm.study("std1").run()
    s11 = np.atleast_1d(m.evaluate("emw.S11")).ravel()
    assert np.all(np.isfinite(s11)) and abs(s11[0]) <= 1.05, s11
