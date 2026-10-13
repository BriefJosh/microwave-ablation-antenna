"""Where to sample the fields, and how to turn them into V(x) and I(x), on the SICL cross-section (y-z plane at fixed x, lengths in mm).
V(x) = integral of Ez from the inner strip up to the top plate along y = 0 (Gauss-Legendre).
I(x) = circulation of H around the strip on a rectangle (half-width ycl, half-height delta), counterclockwise in (y, z), so +x current is positive.
Units: fields in the unit of the model (V/mm and A/mm if lengths are mm), so V and I come out in V and A."""
import numpy as np

def plan(xs, z_inner, z_top, ycl=0.5, delta=0.1, n_v=12, n_g=40):
    if z_inner + delta > z_top - 0.02 or z_inner - delta < 0.02:
        raise ValueError("current loop must stay clear of the plates")
    gx, gw = np.polynomial.legendre.leggauss(n_g)              # nodes on [-1, 1]
    vx, vw = np.polynomial.legendre.leggauss(n_v)
    zv = z_inner + (vx + 1) / 2 * (z_top - z_inner); wv = vw * (z_top - z_inner) / 2
    ya, wy = ycl * gx, ycl * gw                                  # y from -ycl to +ycl
    za, wz = z_inner + delta * gx, delta * gw
    blocks, pts = [], []
    for x in xs:
        p = [(x, 0.0, z) for z in zv]
        p += [(x, y, z_inner - delta) for y in ya]               # bottom edge, +y direction
        p += [(x, ycl, z) for z in za]                           # right edge, +z direction
        p += [(x, y, z_inner + delta) for y in ya]               # top edge, traversed -y: sign applied in integrate
        p += [(x, -ycl, z) for z in za]                          # left edge, traversed -z
        pts += p
    return {"points": np.array(pts, float), "xs": np.array(xs, float), "n_v": n_v, "n_g": n_g, "wv": wv, "wy": wy, "wz": wz, "block": n_v + 4 * n_g}

def integrate(pl, ez, hy, hz):
    nb, nv, ng = pl["block"], pl["n_v"], pl["n_g"]
    ez, hy, hz = (np.asarray(a, complex).reshape(len(pl["xs"]), nb) for a in (ez, hy, hz))
    v = ez[:, :nv] @ pl["wv"]
    b0 = nv; r0 = b0 + ng; t0 = r0 + ng; l0 = t0 + ng
    cur = (hy[:, b0:r0] @ pl["wy"] + hz[:, r0:t0] @ pl["wz"] - hy[:, t0:l0] @ pl["wy"] - hz[:, l0:l0 + ng] @ pl["wz"])
    return {"x": pl["xs"], "V": v, "I": cur}
