import xml.etree.ElementTree as ET
import stackup

def _mat(root, name):
    return next(m for m in root.iter("Material") if m.get("Name") == name)

def test_liver_written_as_conductivity(tmp_path):
    f = tmp_path / "s.xml"; stackup.write(str(f))
    liver = _mat(ET.parse(f).getroot(), "LIVER")
    assert float(liver.get("DielectricLossTangent")) == 0.0
    assert float(liver.get("Conductivity")) == 1.69
    assert float(liver.get("Permittivity")) == 43.2

def test_copper_sheets_at_paper_heights(tmp_path):
    f = tmp_path / "s.xml"; stackup.write(str(f))
    layers = {l.get("Name"): l for l in ET.parse(f).getroot().iter("Layer")}
    assert layers["TOP"].get("Zmin") == layers["TOP"].get("Zmax") == "665"
    assert layers["INNER"].get("Zmin") == "465"
    assert layers["BOTTOM"].get("Zmin") == "0"
    assert layers["VIA"].get("Type") == "via"

def test_bricks_present_for_board_fep_liver(tmp_path):
    f = tmp_path / "s.xml"; stackup.write(str(f))
    types = {l.get("Name"): l.get("Type") for l in ET.parse(f).getroot().iter("Layer")}
    assert types["BOARD"] == types["FEP"] == types["LIVER"] == "dielectric"

def test_lossy_bricks_carry_equivalent_conductivity(tmp_path):
    # gds2palace 0.8.0 drops DielectricLossTangent for drawn (brick) dielectrics, so FR4 and FEP loss is
    # written as sigma = 2*pi*f0*eps0*eps_r*tan_d at f0 = 2.45 GHz (found by the Task 5 spike)
    import math
    f = tmp_path / "s.xml"; stackup.write(str(f))
    root = ET.parse(f).getroot()
    for name, er, td in (("FR4", 4.8, 0.02), ("FEP", 2.1, 0.0003)):
        m = _mat(root, name)
        want = 2 * math.pi * 2.45e9 * 8.8541878128e-12 * er * td
        assert float(m.get("DielectricLossTangent")) == 0.0
        assert abs(float(m.get("Conductivity")) - want) / want < 0.01


def test_air_pad_layer_is_an_air_brick(tmp_path):
    f = tmp_path / "s.xml"; stackup.write(str(f))
    layers = {l.get("Name"): l for l in ET.parse(f).getroot().iter("Layer")}
    assert layers["AIRPAD"].get("Type") == "dielectric" and layers["AIRPAD"].get("Material") == "AIR"
