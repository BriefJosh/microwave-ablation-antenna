Helix via candidates, 2026-10-21. Retuned layout L4 8.0, L2 14.5, L3 72.5 mm, w_inner 0.5 mm; JLCPCB nominal stack 4.4 / 4.23 / 4.4; liver; 50 ohm port; COMSOL physics-controlled mesh index 6; one mesh per case; 0.025 GHz grid (reference 2.30-2.75 GHz, new runs 2.30-2.60 GHz). Margins signed: negative = 2.45 GHz outside the band by that much.

| Case (hole / via diameter, mm) | JLCPCB surcharge | Elements | Solve (s) | Dip (GHz) | Depth (dB) | S11 at 2.45 GHz (dB) | -10 dB band (GHz) | Width (MHz) | Margin of 2.45 GHz (low / high, MHz) | Port Zin at 2.45 GHz (ohm) | CSV |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Square ends (before 2026-10-21), 0.2 / 0.40 | True | 321225 | 732 | 2.4658 | -20.2 | -18.40 | 2.4136 to 2.5114 | 98 | 36.4 / 61.4 | 58.2 + j10.2 | `liver_scan_jlc_L4_8_L2_145_i6.csv` |
| Mitered, 0.2 / 0.40 | True | 320815 | 750 | 2.4686 | -20.5 | -17.56 | 2.4156 to 2.5134 | 98 | 34.4 / 63.4 | 58.3 + j11.8 | `liver_scan_jlc_best_via_0p2_0p40_miter_i6.csv` |
| Mitered, 0.2 / 0.45 | False | 299560 | 730 | 2.4569 | -20.2 | -19.83 | 2.4100 to 2.5064 | 96 | 40.0 / 56.4 | 59.1 + j6.4 | `liver_scan_jlc_best_via_0p2_0p45_miter_i6.csv` |
| Mitered, 0.3 / 0.45 | False | 295856 | 696 | 2.4714 | -22.5 | -17.23 | 2.4165 to 2.5170 | 101 | 33.5 / 67.0 | 56.1 + j13.4 | `liver_scan_jlc_best_via_0p3_0p45_miter_i6.csv` |
| Mitered, 0.4 / 0.50 | False | 357089 | 844 | 2.4749 | -23.0 | -14.94 | 2.4241 to 2.5232 | 99 | 25.9 / 73.2 | 55.0 + j18.4 | `liver_scan_jlc_best_via_0p4_0p50_miter_i6.csv` |
