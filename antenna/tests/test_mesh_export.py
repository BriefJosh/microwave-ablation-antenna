import os, sys, importlib
import numpy as np, pytest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "comsol"))
mesh_export = importlib.import_module("mesh_export")

def test_crop_keeps_only_triangles_inside_window():
    pts = np.array([[0, 0], [1, 0], [0, 1], [5, 5], [6, 5], [5, 6]], float)
    tris = np.array([[0, 1, 2], [3, 4, 5]])
    p, t = mesh_export.crop(pts, tris, (-0.5, 2, -0.5, 2))
    assert len(t) == 1 and len(p) == 3 and t.max() == 2

def test_mesh_counts_match_record():
    with pytest.raises(ValueError, match="index 6"):
        mesh_export.check_count(6, 250000)
    mesh_export.check_count(6, 267299)

def test_slice_tet_gives_triangle_or_quad_at_plane():
    pts = np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0], [0, 0, 1]], float)
    polys = mesh_export.slice_tets(pts, np.array([[0, 1, 2, 3]]), 0.5)
    assert len(polys) == 1 and len(polys[0]) == 3
    assert np.allclose(sorted(map(tuple, np.round(polys[0], 6))), [(0, 0), (0, 0.5), (0.5, 0)])
    pts2 = np.array([[0, 0, -1], [1, 0, -1], [0, 1, 1], [1, 1, 1]], float)   # two below, two above -> quad
    assert len(mesh_export.slice_tets(pts2, np.array([[0, 1, 2, 3]]), 0.0)[0]) == 4
    assert mesh_export.slice_tets(pts, np.array([[0, 1, 2, 3]]), 2.0) == []

def test_crop_polys_by_window():
    polys = [np.array([[0, 0], [1, 0], [0, 1]]), np.array([[5, 5], [6, 5], [5, 6]])]
    assert len(mesh_export.crop_polys(polys, (-0.5, 2, -0.5, 2))) == 1

def test_counts_within_half_a_percent_pass():
    mesh_export.check_count(5, 362525)                       # +0.15 %: re-meshing in one session differs slightly
    with pytest.raises(ValueError):
        mesh_export.check_count(5, 379847)                   # +4.9 %: a different grid top frequency
