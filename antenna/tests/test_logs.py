from analysis import logs

def test_scan_flags_nonconvergence(tmp_path):
    p = tmp_path / "palace.log"; p.write_text("it 400 ... \n  GMRES solver did NOT converge in 400 iterations\n")
    assert logs.scan(p, "palace")
    e = tmp_path / "elmer.log"; e.write_text("ERROR:: IterSolve: Failed convergence tolerances.\n")
    assert logs.scan(e, "elmer")

def test_clean_logs_pass(tmp_path):
    p = tmp_path / "palace.log"; p.write_text("GMRES solver converged in 31 iterations\n")
    assert logs.scan(p, "palace") == []
