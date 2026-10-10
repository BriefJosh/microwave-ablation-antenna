import math
from params import P, derived, dielectric_layers
from shapes import LAYERS

F0 = 2.45e9; EPS0 = 8.8541878128e-12

def sigma_eq(eps_r, tand, f0=F0):
    """gds2palace 0.8.0 drops DielectricLossTangent for drawn (brick) dielectrics; loss is written as the
    equivalent conductivity at f0 (Task 5 spike, 2026-10-10)."""
    return 2 * math.pi * f0 * EPS0 * eps_r * tand

TOPOLOGIES = ("bricks", "liver_background")

def write(path, p=P, topology="bricks"):
    d = derived(p); um = lambda v: str(round(v * 1000))
    zt, zi = d["z_top"], d["z_inner"]
    big = p.liver_margin + 5
    bg = "AIR" if topology == "bricks" else "LIVER"
    # board dielectric: Wen's single FR4 block, or one brick and one material per layer of a layered stack (lower prepreg, core, upper prepreg)
    DL = dielectric_layers(p)
    if len(DL) == 1:
        board_materials = [f'    <Material Name="FR4" Type="Dielectric" Permittivity="{p.eps_fr4}" DielectricLossTangent="0" Conductivity="{sigma_eq(p.eps_fr4, p.tand_fr4):.6g}" Color="80c080"/>']
        board_layers = [f'      <Layer Name="BOARD" Type="dielectric" Zmin="0" Zmax="{um(zt)}" Material="FR4" Layer="{LAYERS["BOARD"]}"/>']
    else:
        board_materials = [f'    <Material Name="DIEL_{L["name"]}" Type="Dielectric" Permittivity="{L["eps"]}" DielectricLossTangent="0" Conductivity="{sigma_eq(L["eps"], L["tand"]):.6g}" Color="80c080"/>' for L in DL]
        layer_names = ("BOARD", "BOARD_CORE", "BOARD_UPPER")
        board_layers = [f'      <Layer Name="{n}" Type="dielectric" Zmin="{um(L["z0"])}" Zmax="{um(L["z1"])}" Material="DIEL_{L["name"]}" Layer="{LAYERS[n]}"/>' for n, L in zip(layer_names, DL)]
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<Stackup schemaVersion="3.1">', '  <Materials>',
        '    <Material Name="AIR" Type="Dielectric" Permittivity="1" DielectricLossTangent="0" Conductivity="0" Color="d0d0d0"/>',
        f'    <Material Name="LIVER" Type="Dielectric" Permittivity="{p.eps_liver}" DielectricLossTangent="0" Conductivity="{p.sigma_liver}" Color="c08080"/>',
        *board_materials,
        f'    <Material Name="FEP" Type="Dielectric" Permittivity="{p.eps_fep}" DielectricLossTangent="0" Conductivity="{sigma_eq(p.eps_fep, p.tand_fep):.6g}" Color="e0e0ff"/>',
        '  </Materials>', '  <ELayers LengthUnit="um">', '    <Dielectrics>',
        f'      <Dielectric Name="background" Material="{bg}" Zmin="{um(-big)}" Zmax="{um(zt + big)}"/>',
        '    </Dielectrics>', '    <Layers>',
        f'      <Layer Name="LIVER" Type="dielectric" Zmin="{um(-p.liver_margin)}" Zmax="{um(zt + p.liver_margin)}" Material="LIVER" Layer="{LAYERS["LIVER"]}"/>',
        f'      <Layer Name="FEP" Type="dielectric" Zmin="{um(-p.fep_t)}" Zmax="{um(zt + p.fep_t)}" Material="FEP" Layer="{LAYERS["FEP"]}"/>',
        f'      <Layer Name="AIRPAD" Type="dielectric" Zmin="0" Zmax="{um(zt)}" Material="AIR" Layer="{LAYERS["AIRPAD"]}"/>',
        *board_layers,
        f'      <Layer Name="BOTTOM" Type="sheet" Zmin="0" Zmax="0" Material="PEC" Layer="{LAYERS["BOTTOM"]}"/>',
        f'      <Layer Name="INNER" Type="sheet" Zmin="{um(zi)}" Zmax="{um(zi)}" Material="PEC" Layer="{LAYERS["INNER"]}"/>',
        f'      <Layer Name="TOP" Type="sheet" Zmin="{um(zt)}" Zmax="{um(zt)}" Material="PEC" Layer="{LAYERS["TOP"]}"/>',
        f'      <Layer Name="VIA" Type="via" Zmin="0" Zmax="{um(zt)}" Material="PEC" Layer="{LAYERS["VIA"]}"/>',
        '    </Layers>', '  </ELayers>', '</Stackup>']
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
