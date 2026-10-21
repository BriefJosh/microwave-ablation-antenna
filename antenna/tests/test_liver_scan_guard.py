"""The pre-solve guard in comsol/liver_scan.py stops a run whose helix vias cannot be drawn; no COMSOL needed."""
from dataclasses import replace
import pytest
import params
import comsol.liver_scan as ls

R = replace(params.JLC, L4=8.0, L3=72.5, L2=14.5)

def test_guard_stops_on_bad_pad():
    with pytest.raises(SystemExit):
        ls.guard(replace(R, helix_pad=0.8))

def test_guard_passes_candidate():
    ls.guard(replace(R, helix_drill=0.2, helix_pad=0.45))

def test_existing_result_is_never_overwritten(monkeypatch):
    # liver_scan_jlc_nominal_i6.csv is a committed result; a run with that tag must stop before COMSOL starts
    monkeypatch.delenv("LIVER_MESH_ONLY", raising=False)
    monkeypatch.setattr(ls.mph, "start", lambda **k: pytest.fail("COMSOL started"))
    with pytest.raises(SystemExit):
        ls.main("jlc_nominal_i6", ["L4=8.0+L3=72.5+L2=14.5"], 6, "set")
