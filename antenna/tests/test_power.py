from analysis import power

def test_power_balance_uses_incident_power():
    # 1 W incident, |S11| = 0.1 -> 0.99 W accepted
    assert power.balance_error(0.99, 0.1, 1.0) < 1e-9
    # Elmer 1 V behind 50 ohm: incident = V^2/(8 R) = 2.5 mW
    assert power.balance_error(0.0025 * 0.99, 0.1, 0.0025) < 1e-9
    assert power.balance_error(0.90, 0.1, 1.0) > 0.05
