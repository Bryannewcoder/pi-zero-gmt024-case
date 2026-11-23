#!/usr/bin/env python3
"""
Pi Zero + GMT024-08 LCD case v4 - Bryan's revision list (2026-11-18).

Built on v3. Four changes, all from Bryan 2026-11-18:

1. PRESS PINS SMALLER (base): pin dia 3.0 -> 2.8 in the documented 2.75
   holes. The v3 press fit (0.25 interference) was too tight to get the
   board on; 2.8 leaves a 0.05 light press - still grips, much easier on.
   (2.7 slip fit was the other candidate; 2.8 is the middle pick.)

2. LID SKIRT CLEARANCE: the v3 skirt was line-to-line on the base
   (inside = base outside exactly) and bound going over. Skirt inside
   and outside both move out 0.4 per side: 0.4 mm of slide clearance
   all round, skirt wall stays 2.2 thick, footprint grows 0.8.

3. LCD GLUES ON TOP (lid): the module no longer lives inside the lid.
   The panel is SOLID - window gone - and the module sits on TOP on
   four raised GLUE PADS at its own screw-hole positions (the v3 HOLES
   centres), 6.0 dia, standing it 3.0 above the panel: the drawing's
   rear "component area Height = 2.5 max" clears with 0.5 to spare.
   The header housing (2.54 proud of the rear) also clears the panel.
   A PIN SLOT through the panel under the header row lets the module's
   8 pins pass through into the box: pins sit 12.47..30.25 from the
   module's west edge (drawing: pin 1 at 12.47, P2.54x(8-1)=17.78) on
   the 2.50 line from its header-end edge; the slot spans the pins
   +/-5.5 in x and the row -3.8/+5.0 in y, so the housing and the
   Dupont plugs have room. Bezel dropped - nothing to frame now.

4. OLD LCD MOUNTINGS REMOVED (lid inside): the underside screw pads,
   their M2 pilots and the south ledge are gone. The lid underside is
   clean; the cavity is open right up to the panel.

Unchanged from v3: footprint, base, Zero press-pin mount positions,
lid port slots (board still flipped, HDMI end front), strip vents,
accent grooves, closure screw pilots, skirt locking band.

Dimensions sources (official documents ONLY):
  Pi Zero : Raspberry Pi Zero datasheet mechanical drawing RPI-ZERO-V1_2
            board 65 x 30, holes 2.75 dia at 3.5 insets (58 x 23 pitch);
            port centres from the board's HDMI end: mini-HDMI 12.4,
            USB 41.4, PWR 54.
  LCD     : GoldenMorning GMT024-08-SPI8P drawing (header pin 1 at
            12.47 from the PCB west edge, 8 pins P2.54 = 17.78 span,
            pin row 2.50 from the header-end edge, rear component area
            2.5 max high, header housing 2.54 proud) + Bryan's
            2026-11-02 caliper measurements (module 43.71 wide x 71.0
            long; hole centres as test-fit in v3).
"""
import numpy as np
import trimesh
from trimesh.creation import box as mkbox, cylinder as mkcyl, cone as mkcone
from pathlib import Path

OUT = Path(__file__).resolve().parent / "out4"
OUT.mkdir(parents=True, exist_ok=True)

# ---------------- frame ----------------
WALL = 2.4
W, D = 76.8, 79.2                 # case footprint (x = E-W, y = N-S, y0 = north)
FLOOR_T = 2.4
LID_UNDER = 33.6                   # underside of the lid panel
LID_TOP = 36.0
SKIRT_BOT = 13.0                   # deep skirt: lid wraps the base to z=13
SCREW_Z = 18.0                     # closure screws (below the LCD's back plane)
SKIRT_CLR = 0.4                    # v4: slide clearance per side, skirt vs base
SKIRT_OUT = 2.2 + SKIRT_CLR        # skirt outer offset (wall stays 2.2 thick)

# ---------------- Pi Zero, standing on its side ----------------
# Board plane vertical, component face EAST, port edge UP.
# HDMI/SD end at the FRONT of the case (y = ZB_Y1 end) per Bryan's
# install photo 2026-11-06 - port centres are measured back from ZB_Y1.
ZB_X0, ZB_X1 = 8.6, 10.0           # board thickness span (centre plane 9.3)
ZB_Y0, ZB_Y1 = 8.5, 73.5           # 65 long; y1 end = the drawing's x=0 (HDMI) end
ZB_Z0, ZB_Z1 = 2.4, 32.4           # 30 wide: bottom edge rests on the floor top
PORT_Y = {"HDMI": ZB_Y1 - 12.4, "USB": ZB_Y1 - 41.4, "PWR": ZB_Y1 - 54.0}
SD_YC = ZB_Y1 - 16.9               # microSD slot centre (approx - generous block)
# mounting holes (documented 3.5 insets, 58 x 23 pitch) as (y, z) pairs
ZB_HOLES = [(ZB_Y0 + 3.5, ZB_Z0 + 3.5), (ZB_Y1 - 3.5, ZB_Z0 + 3.5),
            (ZB_Y0 + 3.5, ZB_Z1 - 3.5), (ZB_Y1 - 3.5, ZB_Z1 - 3.5)]
PIN_R = 1.4                        # v4: 2.8 dia pin in the documented 2.75 hole

# ---------------- LCD on TOP of the lid, portrait, header end NORTH ----------------
M_W, M_L, M_T = 42.72, 71.0, 12.5   # M_L = 71.0 MEASURED on Bryan's module 2026-11-02
MX0, MY0 = 29.7, 4.4               # module west edge / header-end edge (case)
HOLES = [(MX0 + 2.5, MY0 + 2.5), (MX0 + 40.22, MY0 + 2.5),
         (MX0 + 2.5, MY0 + 67.8), (MX0 + 40.22, MY0 + 67.8)]
PAD_R = 3.0                        # v4: glue pads at the module's screw holes
PAD_H = 3.0                        # v4: standoff - clears the 2.5-max rear components
# header (drawing): pin 1 at 12.47 from the module's west edge, 8 pins on
# 2.54 pitch (17.78 span), row on the 2.50 line from the header-end edge
HDR_X0, HDR_X1 = MX0 + 12.47, MX0 + 12.47 + 17.78
HDR_Y = MY0 + 2.5
SLOT_X0, SLOT_X1 = HDR_X0 - 5.5, HDR_X1 + 5.5     # pin slot through the panel
SLOT_Y0, SLOT_Y1 = HDR_Y - 3.8, HDR_Y + 5.0

def B(x0, x1, y0, y1, z0, z1):
    m = mkbox(extents=[x1 - x0, y1 - y0, z1 - z0])
    m.apply_translation([(x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2])
    return m

def CYL_X(r, y, z, x0, x1, sections=24):
    m = mkcyl(radius=r, height=x1 - x0, sections=sections)
    m.apply_transform(trimesh.transformations.rotation_matrix(np.pi / 2, [0, 1, 0]))
    m.apply_translation([(x0 + x1) / 2, y, z]); return m

def CONE_X(rmax, y, z, x0, x1, sections=24):
    """Cone along +x: full radius at x0, apex at x1 (pin lead-in).
    NOTE: trimesh's cone has its origin at the BASE centre (spans
    z 0..height), unlike the centred cylinder - translate by x0, not
    the midpoint. (First v3 build centred it and the four tips floated
    0.35 mm clear of the shafts; the component count caught it.)"""
    m = mkcone(radius=rmax, height=x1 - x0, sections=sections)
    m.apply_transform(trimesh.transformations.rotation_matrix(np.pi / 2, [0, 1, 0]))
    m.apply_translation([x0, y, z]); return m

def CYL_Y(r, x, z, y0, y1, sections=20):
    m = mkcyl(radius=r, height=y1 - y0, sections=sections)
    m.apply_transform(trimesh.transformations.rotation_matrix(np.pi / 2, [1, 0, 0]))
    m.apply_translation([x, (y0 + y1) / 2, z]); return m

def CYL_Z(r, x, y, z0, z1, sections=24):
    m = mkcyl(radius=r, height=z1 - z0, sections=sections)
    m.apply_translation([x, y, (z0 + z1) / 2]); return m

def slash(cx, cy, cz, length=9.0, wdt=2.2, depth=4.4, ang=30.0, axis="z"):
    """Diagonal slot cutter. axis='z': slot in a horizontal panel (rotates
    in plan). axis='y': through a N/S wall. axis='x': through an E/W wall."""
    m = mkbox(extents=[length, wdt, depth])
    if axis == "z":
        m.apply_transform(trimesh.transformations.rotation_matrix(
            np.radians(ang), [0, 0, 1]))
    elif axis == "y":
        m = mkbox(extents=[length, depth, wdt])
        m.apply_transform(trimesh.transformations.rotation_matrix(
            np.radians(ang), [0, 1, 0]))
    else:
        m = mkbox(extents=[depth, length, wdt])
        m.apply_transform(trimesh.transformations.rotation_matrix(
            np.radians(ang), [1, 0, 0]))
    m.apply_translation([cx, cy, cz]); return m

def edge_bevels(w, d, z0, c=3.54):
    """45-degree edge breaks: square-section cutters rotated to diamonds,
    centred on each horizontal edge line (N/S edges run along x, E/W along y)."""
    cuts = []
    L = max(w, d) + 8
    for cy in (0.0, d):
        m = mkbox(extents=[L, c, c])
        m.apply_transform(trimesh.transformations.rotation_matrix(np.radians(45), [1, 0, 0]))
        m.apply_translation([w / 2, cy, z0]); cuts.append(m)
    for cx in (0.0, w):
        m = mkbox(extents=[c, L, c])
        m.apply_transform(trimesh.transformations.rotation_matrix(np.radians(45), [0, 1, 0]))
        m.apply_translation([cx, d / 2, z0]); cuts.append(m)
    return cuts

# ================= BASE =================
base = B(0, W, 0, D, 0, LID_UNDER)
cavity = B(WALL, W - WALL, WALL, D - WALL, FLOOR_T, LID_UNDER + 1)
cuts = [cavity]
# wall vents: south wall slashes (intake, under the LCD cavity)
for i in range(7):
    cuts.append(slash(33 + i * 5.5, D - WALL / 2, 7.5, axis="y"))
# west wall slashes (intake beside the standing Zero) - 5 (v3: the 6th
# at y=65.5 ran into the y=70 mount boss pad)
for i in range(5):
    cuts.append(slash(WALL / 2, 38 + i * 5.5, 7.5, axis="x"))
cuts += edge_bevels(W, D, 0.0)                     # bottom edge bevels
for c in cuts:
    base = base.difference(c)
# --- Zero mount (AFTER the cavity/vent cuts): one boss pad + press pin
# per documented mounting hole, on the west wall. Nothing stands in the
# board's drop path; the header pins / Dupont plugs get the open cavity.
for (hy, hz) in ZB_HOLES:
    base = base.union(CYL_X(4.5, hy, hz, WALL - 0.4, ZB_X0))       # boss pad
    base = base.union(CYL_X(PIN_R, hy, hz, ZB_X0 - 1.0, ZB_X1 + 1.4))  # pin shaft
    # lead-in cone OVERLAPS the shaft end by 0.5 - a cone that only touches
    # the shaft on its base face is a separate shell (the v2.0 lid lesson)
    base = base.union(CONE_X(PIN_R, hy, hz, ZB_X1 + 0.9, ZB_X1 + 2.6))
# closure screw pilots through the south + north walls (skirt handled on lid)
for x in (20.0, 55.0):
    base = base.difference(CYL_Y(1.1, x, SCREW_Z, D - WALL - 0.1, D + 0.1))
for x in (20.0, 72.0):
    base = base.difference(CYL_Y(1.1, x, SCREW_Z, -0.1, WALL + 0.1))

# ================= LID =================
lid = B(0, W, 0, D, LID_UNDER, LID_TOP)
# skirt: ring up to LID_UNDER, then a 1.4 mm locking band that bites 3.0 mm
# into the panel's footprint so skirt and panel overlap volumetrically.
# v4: inner AND outer faces move out by SKIRT_CLR (wall stays 2.2 thick).
sk_out = B(-SKIRT_OUT, W + SKIRT_OUT, -SKIRT_OUT, D + SKIRT_OUT, SKIRT_BOT, LID_UNDER + 1.4)
sk_in = B(-SKIRT_CLR, W + SKIRT_CLR, -SKIRT_CLR, D + SKIRT_CLR, SKIRT_BOT - 1, LID_UNDER)
sk_in2 = B(3.0, W - 3.0, 3.0, D - 3.0, LID_UNDER, LID_UNDER + 1.5)
lid = lid.union(sk_out.difference(sk_in).difference(sk_in2))
# v4: four glue pads ON TOP at the module's screw-hole positions. Each
# pad starts 1.0 BELOW the panel top so the union overlaps volumetrically
# (a pad that only kisses the panel face is a separate shell).
for (hx, hy) in HOLES:
    lid = lid.union(CYL_Z(PAD_R, hx, hy, LID_TOP - 1.0, LID_TOP + PAD_H))

cuts = []
# v4: pin slot through the panel under the LCD header row (the screen
# window and the internal LCD pads/pilots/ledge are GONE - panel solid)
cuts.append(B(SLOT_X0, SLOT_X1, SLOT_Y0, SLOT_Y1, LID_UNDER - 1, LID_TOP + 1))
# port slots in the lid's west strip - board flipped: HDMI alone at the
# front (its flipped position); USB+PWR as one bay at the back.
cuts.append(B(3.4, 15.6, PORT_Y["HDMI"] - 6.5, PORT_Y["HDMI"] + 6.5,
              LID_UNDER - 1, LID_TOP + 1))
cuts.append(B(3.4, 15.6, PORT_Y["PWR"] - 6.5, PORT_Y["USB"] + 6.5,
              LID_UNDER - 1, LID_TOP + 1))
# exhaust slash vents in the strip east of the port slots (over the channel)
for i in range(9):
    cuts.append(slash(21.7, 13 + i * 6.8, (LID_UNDER + LID_TOP) / 2, axis="z"))
# accent grooves on the panel's south margin (blind)
for gy in (75.6, 77.2):
    cuts.append(B(32, 70, gy, gy + 0.9, LID_TOP - 0.8, LID_TOP + 0.1))
# skirt screw pilots (continue the base pilots through the skirt; v4:
# outer ends extended to clear the moved-out skirt face)
for x in (20.0, 55.0):
    cuts.append(CYL_Y(1.1, x, SCREW_Z, D - 0.1, D + SKIRT_OUT + 0.1))
for x in (20.0, 72.0):
    cuts.append(CYL_Y(1.1, x, SCREW_Z, -SKIRT_OUT - 0.1, 0.1))
cuts += edge_bevels(W, D, LID_TOP, c=2.0)          # lid top edge bevels (c=2.0: bigger pinches the skirt band)
# skirt bottom bevel ring (diamond cutters on the skirt's outer edge lines;
# v4: edge lines move out with the skirt face)
skb = []
L = max(W, D) + 14
for cy in (-SKIRT_OUT, D + SKIRT_OUT):
    m = mkbox(extents=[L, 3.54, 3.54])
    m.apply_transform(trimesh.transformations.rotation_matrix(np.radians(45), [1, 0, 0]))
    m.apply_translation([W / 2, cy, SKIRT_BOT]); skb.append(m)
for cx in (-SKIRT_OUT, W + SKIRT_OUT):
    m = mkbox(extents=[3.54, L, 3.54])
    m.apply_transform(trimesh.transformations.rotation_matrix(np.radians(45), [0, 1, 0]))
    m.apply_translation([cx, D / 2, SKIRT_BOT]); skb.append(m)
cuts += skb
for c in cuts:
    lid = lid.difference(c)

# ================= export =================
def save(mesh, name):
    mesh.export(OUT / name)
    print(f"{name}: watertight={mesh.is_watertight} vol={mesh.volume/1000:.1f} cm3")

save(base, "base.stl"); save(lid, "lid.stl")
asm = trimesh.util.concatenate([base, lid])
save(asm, "assembly_preview.stl")
print(f"overall: {W} x {D} x {LID_TOP} mm (skirt {W+2*SKIRT_OUT} x {D+2*SKIRT_OUT}, clearance {SKIRT_CLR}/side)")
print(f"header pins x {HDR_X0:.2f}..{HDR_X1:.2f} at y={HDR_Y:.2f}; slot x {SLOT_X0:.2f}..{SLOT_X1:.2f}, y {SLOT_Y0:.2f}..{SLOT_Y1:.2f}")
print(f"glue pads r{PAD_R} h{PAD_H} at {HOLES}")
print(f"Zero holes (y,z): {ZB_HOLES}  pin dia: {2*PIN_R:.2f} in 2.75 holes")
