"""Wen et al. 2021, IEEE AWPL 20(5):713-717, DOI 10.1109/LAWP.2021.3061006.
One source of truth for the three-solver gate. Units mm. Coordinates: x along the antenna from the
feed port (x=0) to the tip, y across the width (paper's x), z up from the bottom copper (z=0).
Copper is a zero-thickness sheet in every solver (simulation choice; the fab board keeps 1 oz)."""
import math
from dataclasses import dataclass, replace

@dataclass(frozen=True)
class Wen2021:
    h_top: float = 0.2
    h_bond: float = 0.265
    h_bot: float = 0.2
    t_cu_outer: float = 0.035
    t_cu_inner: float = 0.0175
    sigma_cu: float = 5.8e7
    eps_fr4: float = 4.8
    tand_fr4: float = 0.02
    eps_layers: tuple = ()    # per dielectric layer, bottom to top; empty = one FR4 block (Wen). JLC: (prepreg, core, prepreg)
    tand_layers: tuple = ()
    a: float = 2.8
    w_inner: float = 0.5
    d_feed: float = 0.5
    D_antipad: float = 1.0
    fence_drill: float = 0.4
    fence_pitch: float = 0.6
    sicl_len: float = 54.0
    L1: float = 17.0
    L2: float = 12.5
    W1: float = 3.7
    W6: float = 1.3
    paddle_w: float = 10.6
    pad_end_gap: float = 0.55
    feed_via_inset: float = 0.5
    feed_inner_pad: float = 0.9
    L3: float = 70.5
    L4: float = 6.0
    L5: float = 0.608
    L6: float = 14.5
    L7: float = 2.745
    W4: float = 3.4
    W5: float = 0.2
    theta_deg: float = 77.173
    helix_pad: float = 0.4
    helix_drill: float = 0.2
    n_helix_steps: int = 13   # Fig. 4b: 14 pads per row (13 steps). The text's 49.4 mm arm needs 12 steps and no tip bar; see helix_tip_bar
    helix_tip_bar: bool = True  # Fig. 4b: a 14th bar per layer ends free beyond the last via pad (no via)
    plate_w: float = 3.2
    wedge_len: float = 2.5
    fep_t: float = 0.35
    eps_fep: float = 2.1
    tand_fep: float = 0.0003
    eps_liver: float = 43.2
    sigma_liver: float = 1.69
    liver_start_from_paddle: float = 20.0
    liver_margin: float = 30.0
    air_margin: float = 5.0

P = Wen2021()

# JLCPCB 4-layer stack JLC04081H-7628 (order form 2026-10-05: prepreg 0.2104 / core 0.25 / prepreg 0.2104 mm, copper 0.035 / 0.0152 / 0.0152 / 0.035 mm), L3 left empty.
# NP-155F permittivity as JLCPCB's impedance calculator states it (prepreg 4.4, core 4.23; no frequency given). Nan Ya's datasheet (2025-10-27) gives 4.2-4.4 for the laminate and 3.9-4.1 for
# the thin laminate at 1 GHz, so 3.9-4.4 is the plausible range; loss tangent 0.014 is inside its 1 GHz ranges (0.012-0.016). The order form's default is unbranded FR4 TG135, laminate not stated. Wen's inner conductor sits 0.2 mm below the top, here L2 at 0.2104 mm: the layout carries over unchanged.
JLC = replace(P, h_top=0.2104, h_bond=0.25, h_bot=0.2104, t_cu_inner=0.0152, eps_layers=(4.4, 4.23, 4.4), tand_layers=(0.014, 0.014, 0.014))

SOURCES = {
    "t_cu_outer": "S II.A", "t_cu_inner": "S II.A / T1 t", "sigma_cu": "assumption (annealed copper, 5.8e7 S/m)",
    "h_top": "S II.A", "h_bond": "S II.A", "h_bot": "S II.A", "eps_fr4": "S II.A", "tand_fr4": "S II.A",
    "a": "T1 a = T2 W2 (fence-row centre spacing, Fig.4b)", "w_inner": "T1 w = T2 W3",
    "d_feed": "T1 d", "D_antipad": "T1 D", "fence_drill": "T1 R1, a diameter per S II.A",
    "fence_pitch": "T1 p", "sicl_len": "S II.B '54 mm long SICL'",
    "L1": "T2 (feed paddle length, Fig.4a)", "L2": "T2 + S II.B '12.5 mm long microstrip'",
    "W1": "T2", "W6": "T2 (launch strip width, Fig.4a)",
    "paddle_w": "F Fig.4a scale: L2 455 px = 12.5 mm, paddle 385 px (assumption)",
    "pad_end_gap": "F Fig.4a (assumption)", "feed_via_inset": "assumption (via fully under pad)",
    "feed_inner_pad": "assumption (inner-layer pad on the feed via)",
    "L3": "T2", "L4": "T2", "L5": "T2 (via spacing along a row, Fig.4b inner layer)", "L6": "T2 + S II.B 14.5 mm",
    "L7": "T2 (via-row spacing)", "W4": "T2 (board width)", "W5": "T2 (arm trace width)",
    "theta_deg": "T2", "helix_pad": "T2 R2 (pad diameter, Fig.4b)",
    "helix_drill": "assumption (JLCPCB-feasible drill in a 0.4 pad)",
    "n_helix_steps": "F Fig.4b: 14 pads per row (13 steps). Provisional baseline since 2026-10-12: the text's 49.4 mm arm (S II.B) gives 12 steps",
    "helix_tip_bar": "F Fig.4b: 14 full bars per layer, the last one dangling. Provisional baseline since 2026-10-12 (COMSOL dip 2.434 GHz)",
    "plate_w": "D: W2 + R1 so plates cover the fence vias", "wedge_len": "F Fig.4b (assumption)",
    "fep_t": "S II.B", "eps_fep": "assumption (typical FEP)", "tand_fep": "assumption",
    "eps_layers": "JLCPCB order form / impedance calculator 2026-10-05 and 2026-10-10 (NP-155F prepreg 4.4, core 4.23); empty for the Wen stack",
    "tand_layers": "0.014 lies inside Nan Ya's datasheet range at 1 GHz (NP-155FR 0.014-0.016, thin NP-155FTL 0.012-0.014; read 2026-10-12, issued 2025-10-27); no value at 2.45 GHz and none for the prepreg",
    "eps_liver": "S III", "sigma_liver": "S III",
    "liver_start_from_paddle": "assumption (insertion depth not stated)",
    "liver_margin": "assumption (about 1.4 field 1/e depths at 2.45 GHz)", "air_margin": "assumption",
}

def derived(p: Wen2021 = P) -> dict:
    d = {}
    d["z_bot"] = 0.0
    d["z_inner"] = p.h_bot + p.h_bond
    d["z_top"] = d["z_inner"] + p.h_top
    d["x_pad_end"] = p.L1 - p.pad_end_gap
    d["x_launch_end"] = d["x_pad_end"] - p.L2
    d["x_feed_via"] = d["x_pad_end"] - p.feed_via_inset
    d["x_sicl0"] = p.L1
    d["x_sicl1"] = p.L1 + p.sicl_len
    d["x_inner_end"] = d["x_sicl1"] + p.L6
    d["y_row"] = p.L7 / 2
    half_slant = d["y_row"] / math.tan(math.radians(p.theta_deg))
    d["x_helix0"] = d["x_sicl1"] + p.L4 + half_slant
    d["n_vias_per_row"] = p.n_helix_steps + 1
    d["x_helix_end"] = d["x_helix0"] + p.n_helix_steps * p.L5
    d["trace_len"] = math.hypot(p.L7, p.L5)
    d["trace_angle_deg"] = math.degrees(math.atan2(p.L7, p.L5))
    via_h = d["z_top"] - d["z_bot"]
    partial = math.hypot(d["y_row"], half_slant)
    d["arm_len"] = p.L4 + partial + (p.n_helix_steps + (1 if p.helix_tip_bar else 0)) * (d["trace_len"] + via_h)
    d["x_wedge0"] = d["x_sicl0"] + p.L3
    d["x_tip"] = d["x_wedge0"] + p.wedge_len
    d["x_liver0"] = p.L1 + p.liver_start_from_paddle
    return d

def dielectric_layers(p: Wen2021 = P) -> list:
    """Dielectric blocks from the bottom plane to the top plane. Wen: one FR4 block. A layered stack (eps_layers set) gives lower prepreg, core, upper prepreg."""
    d = derived(p)
    if not p.eps_layers:
        return [dict(name="FR4", z0=d["z_bot"], z1=d["z_top"], eps=p.eps_fr4, tand=p.tand_fr4)]
    z = [d["z_bot"], d["z_bot"] + p.h_bot, d["z_inner"] + 0.0, d["z_top"]]
    z[2] = p.h_bot + p.h_bond   # core top = inner conductor plane
    names = ("PREPREG_LOWER", "CORE", "PREPREG_UPPER")
    return [dict(name=n, z0=z[i], z1=z[i + 1], eps=p.eps_layers[i], tand=p.tand_layers[i]) for i, n in enumerate(names)]

def derived_full(p: Wen2021 = P) -> dict:
    """z levels of the real-copper stack: bottom Cu / FR4 0.2 / inner Cu / bonding 0.265 / FR4 0.2 / top Cu. The plate-to-plate
    height is 0.2 + 0.0175 + 0.265 + 0.2 = 0.6825 mm (Table I b = 0.7 mm); the zero-thickness model uses 0.665 mm."""
    f = {}
    f["z_bot_cu0"], f["z_bot_cu1"] = -p.t_cu_outer, 0.0
    f["z_inner_cu0"] = p.h_bot
    f["z_inner_cu1"] = f["z_inner_cu0"] + p.t_cu_inner
    f["z_top_cu0"] = f["z_inner_cu1"] + p.h_bond + p.h_top
    f["z_top_cu1"] = f["z_top_cu0"] + p.t_cu_outer
    f["via_z0"], f["via_z1"] = f["z_bot_cu0"], f["z_top_cu1"]
    return f
