import numpy as np

def balance_error(p_abs, s11_mag, p_inc):
    acc = p_inc * (1 - s11_mag ** 2)
    return abs(p_abs - acc) / acc

def absorbed_from_vtu(path, sigma_by_attr, e_re="E_real", e_im="E_imag", attr="attribute"):
    """Sum over tets of 0.5*sigma*|E|^2*volume, E taken as the mean of the tet's nodal values (peak phasor).
    Units: points in the file's length unit (gds2palace: um); volume converted with `UNIT` below."""
    import meshio
    m = meshio.read(path)
    pts = m.points * UNIT; tot = 0.0
    er = m.point_data[e_re]; ei = m.point_data[e_im]
    for blk, attrs in zip(m.cells, m.cell_data[attr]):
        if blk.type != "tetra": continue
        c = blk.data; a = np.asarray(attrs).ravel()
        sig = np.array([sigma_by_attr.get(int(k), 0.0) for k in a])
        if not sig.any(): continue
        v = np.abs(np.einsum("ij,ij->i", pts[c[:, 1]] - pts[c[:, 0]],
                             np.cross(pts[c[:, 2]] - pts[c[:, 0]], pts[c[:, 3]] - pts[c[:, 0]]))) / 6
        e2 = (np.abs(er[c].mean(axis=1)) ** 2).sum(axis=1) + (np.abs(ei[c].mean(axis=1)) ** 2).sum(axis=1)
        tot += float(np.sum(0.5 * sig * e2 * v))
    return tot

UNIT = 1e-6   # metres per mesh unit (gds2palace settings['unit'] = 1e-6)
