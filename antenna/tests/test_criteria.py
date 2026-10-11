import numpy as np
from analysis import criteria
from tests.test_metrics import _notch

def test_all_pass_on_matching_curves():
    c = {k: _notch(2.45e9) for k in ("comsol", "elmer", "palace", "paper_sim")}
    rows = criteria.evaluate(c, refine={"elmer": (2.45e9, 2.452e9), "palace": (2.45e9, 2.449e9), "comsol": (2.45e9, 2.451e9)},
                             logs_ok={"elmer": True, "palace": True, "comsol": True},
                             power_err={"elmer": 0.01, "palace": 0.02, "comsol": 0.01})
    assert all(r.passed for r in rows), [r for r in rows if not r.passed]

def test_open_solver_off_by_3_percent_fails():
    c = {"comsol": _notch(2.45e9), "elmer": _notch(2.45e9 * 1.03), "palace": _notch(2.45e9), "paper_sim": _notch(2.45e9)}
    rows = criteria.evaluate(c, refine={}, logs_ok={}, power_err={})
    assert any((not r.passed) and "elmer" in r.name for r in rows)

def test_missing_band_edge_is_a_fail_row_not_a_crash():
    flat = (np.linspace(2e9, 3e9, 11), np.full(11, 0.5 + 0j))
    rows = criteria.evaluate({"comsol": _notch(), "elmer": flat, "palace": _notch(), "paper_sim": _notch()}, {}, {}, {})
    assert any((not r.passed) and "band" in r.name and "elmer" in r.name for r in rows)
