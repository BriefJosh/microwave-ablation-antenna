import os, sys, importlib
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "comsol"))
mp = importlib.import_module("mesh_plots")

def test_windows_cover_the_helix_and_the_board():
    import params
    from params import derived
    w = mp.windows(params.P)
    d = derived(params.P)
    assert w["board"][0] <= 0 and w["board"][1] >= d["x_tip"]
    assert w["helix"][1] >= d["x_tip"] and w["helix"][0] > 0.5 * d["x_tip"]      # the radiator end only
    assert w["helix"][3] - w["helix"][2] < 8                                    # a zoom, a few mm across

def test_pixels_keep_the_window_aspect():
    wpx, hpx = mp.pixels((0, 40, -2, 2), 1200)
    assert wpx == 1200 and abs(hpx - 120) <= 1

def test_patch_is_a_few_mm_inside_the_helix():
    import params
    from params import derived
    w = mp.windows(params.P); d = derived(params.P)
    x0, x1, y0, y1 = w["patch"]
    assert d["x_helix0"] - 0.5 <= x0 < x1 <= d["x_helix_end"] and 3 <= x1 - x0 <= 6

def test_board_window_holds_the_whole_outline():
    import params, shapes
    b = [q for q in shapes.build(params.P)[0] if q.layer == "BOARD"][0]
    x0, x1, y0, y1 = mp.windows(params.P)["board"]
    assert y0 <= min(y for _, y in b.pts) and y1 >= max(y for _, y in b.pts)
