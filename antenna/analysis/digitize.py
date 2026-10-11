import numpy as np
from PIL import Image

def curve(png, color_rgb, tol, x_px, x_val, y_px, y_val):
    """Per image column, the mean row of pixels within `tol` of `color_rgb`, mapped linearly with two calibration
    ticks per axis (x_px/y_px pixel positions, x_val/y_val the axis values at those ticks)."""
    a = np.asarray(Image.open(png).convert("RGB")).astype(float)
    mask = np.linalg.norm(a - np.array(color_rgb, float), axis=2) < tol
    cols = np.where(mask.any(axis=0))[0]
    rows = np.array([np.nonzero(mask[:, c])[0].mean() for c in cols])
    kx = (x_val[1] - x_val[0]) / (x_px[1] - x_px[0]); ky = (y_val[1] - y_val[0]) / (y_px[1] - y_px[0])
    return x_val[0] + (cols - x_px[0]) * kx, y_val[0] + (rows - y_px[0]) * ky
