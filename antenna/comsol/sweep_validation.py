import os, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import mph, validate_microstrip as V
c = mph.start(cores=4)
for label, kw in (("idx5 box y15 z10 (test)", dict(mesh_index=5)), ("idx5 box y30 z25", dict(mesh_index=5, box=(30.0, 25.0))),
                  ("idx3 box y15 z10", dict(mesh_index=3))):
    f, s11, s21 = V.run(client=c, **kw)
    print(label, "| S11 dB:", " ".join("%.1f" % (20 * np.log10(abs(x))) for x in s11), "| S21 dB:", " ".join("%.2f" % (20 * np.log10(abs(x))) for x in s21), flush=True)
