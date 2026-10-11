import numpy as np
from PIL import Image, ImageDraw
from analysis import digitize

def test_recovers_a_straight_red_line(tmp_path):
    im = Image.new("RGB", (200, 100), "white"); d = ImageDraw.Draw(im)
    d.line([(10, 90), (190, 10)], fill=(255, 0, 0), width=2)
    p = tmp_path / "t.png"; im.save(p)
    x, y = digitize.curve(str(p), (255, 0, 0), 60, x_px=(10, 190), x_val=(0.0, 1.0), y_px=(90, 10), y_val=(0.0, 1.0))
    assert np.max(np.abs(y - x)) < 0.03
