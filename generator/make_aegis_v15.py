#!/usr/bin/env python3
"""
Aegis elbow exo v6 (Velcro saddles, end stops, chest plate, hinged wrist module). RIGHT ARM: +X = your right - built around the DSSERVO DS51150. PLACEHOLDER geometry, millimetres.
Frame: elbow axis = X axis through origin, +X = outer (lateral) side, +Z = toward shoulder,
-Z = toward hand, +Y = forward (forearm flexes toward +Y).
ALL "PLACEHOLDER" numbers must be replaced from the manufacturer drawing / your own measurements.
Wrist servo is OPTIONAL: the elbow works without any wrist part.
"""
import math, os, sys
import numpy as np, trimesh
from manifold3d import CrossSection, FillRule, Manifold

# ---------------- arm (MEASURE) ----------------
UPPER_ARM_CIRC = 240.0
FOREARM_CIRC   = 220.0
CLEAR, WALL    = 3.0, 4.0          # cuff slip clearance / wall
PLATE_T, PLATE_W = 8.0, 56.0       # lateral plate thickness / width (Y)
UPPER_CUFF_LEN, FOREARM_CUFF_LEN = 90.0, 80.0
ARC_HALF = 70.0      # saddle covers +/-70 deg around the outer (+X) side of the limb
STRAP_W = 25.0       # Velcro strap width (match your strap)
GAP_UP, GAP_DN = 40.0, 55.0        # saddle edge to elbow axis; sweep-tested: first contact ~110 deg flexion
# ---------------- DS51150 (envelope from vendor page; mounting holes NOT confirmed) --------
SV_L, SV_W, SV_H = 65.0, 30.0, 48.0   # length(Z), width(Y), height(X)
SV_SHAFT_END   = 16.5                 # PLACEHOLDER shaft distance from near end of body
SV_CLEAR       = 0.8                  # per-side slip clearance around the servo body (printed pocket; 0.8 suits a typical FDM A1 print)
CRADLE_WALL    = 5.0
CRADLE_H       = SV_H - 14.0          # wall height (shaft boss/horn stands above it)
EAR_Y, EAR_Z   = 10.0, 75.0           # PLACEHOLDER ear-hole spacing (check drawing): holes at Y=+-EAR_Y, Z=+-EAR_Z/2 about the servo centre
EAR_PILOT_D    = 3.4                  # M4 self-tapping pilot (use 5.6 for M4 heat-set insert)
EAR_PILOT_DEPTH= 24.0
HORN_STACK     = 4.0                  # servo top to underside of link plate
LINK_T, LINK_W = 8.0, 30.0
BOLT_Z         = (-55.0, -80.0)       # link-to-fin bolt rows
FIN_T, FIN_Y   = 8.0, 11.0            # fin thickness, fin centre offset from mid-plane
# ---------------- optional wrist servo (MG996R-class envelope, PLACEHOLDER) --
WS_L, WS_W, WS_H = 40.7, 19.7, 42.9
FOREARM_LEN = 250.0     # elbow axis to wrist axis (MEASURE)
BED = 250.0             # usable A1 print volume per axis (256 nominal, 3 mm margin each side)
RAIL_LEN = FOREARM_LEN-15.0-(GAP_DN+FOREARM_CUFF_LEN)   # rail ends 15 mm short of the wrist axis
# ---------------- chest plate + electronics tray (RIGHT-ARM build; MEASURE chest) ----------
CHEST_CIRC = 850.0      # PLACEHOLDER chest circumference (measure at nipple line)
CHEST_FOAM = 10.0       # space for foam padding
CHEST_T    = 5.0        # plate wall
CHEST_W, CHEST_H = 200.0, 150.0
PAD_X, PAD_Z = 55.0, (35.0, 115.0)     # flat mounting pad for the tray
PATTERN = (80.0, 40.0)                  # tray screw pattern (x, z) -- heat-set M3
TRAY_IN = (110.0, 70.0, 35.0)           # tray inside L x W x H (PLACEHOLDER: size to your battery/PSU)
TRAY_WALL, TRAY_FLOOR = 3.0, 3.0
ESTOP_D = 22.3          # standard 22 mm pushbutton
# ---------------- hinged wrist module (OPTIONAL; hand frame: forearm pronated, palm down, dorsum faces +Y) ----
HAND_LEN, HAND_W, HAND_T = 195.0, 85.0, 30.0   # wrist joint to middle fingertip (given), hand width / thickness (PLACEHOLDER)
DORSAL_FOAM = 5.0
WRIST_Z   = -FOREARM_LEN        # wrist axis (pin along X through y=0)
LIM_FLEX, LIM_EXT = 55.0, 45.0  # wrist mechanical limits (deg) set by the arc slot
PIN_D, ARC_R = 5.0, 17.0        # M5 pivot / stop bolt, stop-slot radius
BOLT_Y = -17.0                  # stop bolt sits this far from the pivot, on the forearm ear
LEVER_A = 28.0                  # drive-pin lever arm on the hand piece
RC, ROD = 30.0, 67.0            # crank length, rod length (centre to centre)
WS_L, WS_W, WS_H = 40.7, 19.7, 42.9
WS_SHAFT_END = 10.5             # PLACEHOLDER: wrist-servo shaft distance from its near end

# ---------------- CHEST SUPPORT (arm <-> chest link) ----------------
# Load path: forearm+servo weight -> upper saddle -> shoulder strut -> gimbal block -> arch yoke -> chest plate -> torso straps.
# The strut pivots about X (shoulder flexion/extension free) and the yoke pivots about Y (abduction free), so the arm moves freely;
# the elbow's own reaction torque is NOT sent to the chest (it is an internal force pair across the elbow, carried by the arm's own straps).
UPPER_ARM_LEN   = 290.0     # elbow axis to shoulder pivot (MEASURE)
CHEST_AXIS_X    = -165.0    # torso centre line, in the elbow frame (x, lateral). MEASURE: shoulder-pivot to sternum distance
CHEST_PLATE_Z0  = 115.0     # height of the chest plate's bottom edge above the elbow axis (plate top sits ~25 mm below the shoulder)
STRUT_HOLES_Z   = (75.0, 115.0)
STRUT_INSERT_D, STRUT_INSERT_DEPTH = 5.6, 6.5
STRUT_BOLT_D    = 4.3
STRUT_Z0, STRUT_W, STRUT_T = 62.0, 32.0, 8.0
# ---------------- UPPER-ARM ROLL (rotation about the humerus axis) ----------------
# A curved T-rail bolted to the top of the upper saddle, concentric with the arm axis, slides through a curved T-slot in the strut's foot (the carriage).
# The strut stays with the chest link while the arm (saddle + rail) rolls about its own long axis, so the rail travel IS the roll range.
ROLL_RC     = 50.5          # rail centreline radius from the arm axis
ROLL_HALF   = 32.0          # rail half-span (deg) = roll range each way
ROLL_Z0     = 130.0         # top face of the saddle plate (rail seat)
RAIL_STEM   = 3.0           # stem half-width (radial)
RAIL_HEAD   = 6.0           # head half-width (radial)
RAIL_STEM_H, RAIL_HEAD_H = 10.0, 8.0   # stem height, head height
SLIDE_CLR   = 0.4           # slide clearance per side
ROLL_SCREW_ANG = (-20.0, 0.0, 20.0)
ROLL_SCREW_D, ROLL_PILOT_D, ROLL_PILOT_DEPTH = 4.3, 3.4, 14.0
CARR_X0, CARR_ZTOP, CARR_Y = 41.0, 153.6, 16.0
BLOCK = (24.0, 26.0)        # gimbal block size in X, Y
FOOT_PHI_X, FOOT_Z = 79.0, 75.0   # foot centre on the chest plate (plate frame): lateral offset, height
FOOT_HOLES = 11.0           # foot bolt pattern half-spacing (square, 22 mm)
# ---------------- end stops (fixed to the upper-arm cradle, hit by the forearm torque fins) ------
FLEX_LIMIT_DEG = 90.0      # target flexion stop (cuff-to-cuff contact is ~110)
EXT_POST_Y     = -15.6      # inner face of the extension post (fin face is at y=-15)
FLEX_BLOCK_Y   = 43.0       # how far the flexion block reaches in +Y (tuned by sweep)
FLEX_BLOCK_Z   = (0.0, 80.0)
# secondary (backup) stops on the saddle plates themselves: engage ~2 deg after the primary stops
EXT2_TAB_Z     = -54.0      # bottom of the tab hanging from the upper saddle plate (-Y edge); engages ~-3 deg
FLEX2_Y        = 44.0       # reach of the backup flexion block on the upper saddle plate; engages ~107 deg
FLEX2_Z        = (18.0, 46.0)
PRIMARY=True; BACKUP=True   # test switches
STOP_X         = (53.2, 93.2)   # x-span of both stops (overlaps the fin x-range 46-105)
SEG = 96
# ---------------- WIRING (v15) ----------------
# DS51150 datasheet (DSSERVO/ANNIMOS): connector lead 300 +-5 mm (VERIFIED). JR 3-pin connector housing is ~8 x 3 mm.
# Where the lead leaves the servo body is NOT in the text datasheet -> PLACEHOLDER: assumed out of the +Z end (toward the shoulder). CHECK.
LEAD_NOTCH_W, LEAD_NOTCH_H = 12.0, 8.0     # wire exit notch through the cradle end wall (y width, x height measured from pocket floor)
CLIP_D_IN, CLIP_WALL, CLIP_SLIT = 7.0, 2.0, 3.5   # cable clip: bore for a 2-wire lead + ties, wall, snap-in slit
EAR_SLOT = 6.0                              # ear-hole slots are this long (total) along Z so a wrong pitch still bolts in
ZIP_W, ZIP_T = 4.2, 2.0                     # zip-tie slot (fits 3.6 x 1.2 mm ties)
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)),"out"); os.makedirs(OUT,exist_ok=True)

def cube(x,y,z,c=(0,0,0)): return Manifold.cube([x,y,z],center=True).translate(list(c))
def box(x0,x1,y0,y1,z0,z1): return cube(x1-x0,y1-y0,z1-z0,((x0+x1)/2,(y0+y1)/2,(z0+z1)/2))

def _sp(r,c): return Manifold.sphere(r,24).translate(list(c))
def rbox(x0,x1,y0,y1,z0,z1,r=3.0):
    """box with every edge rounded (hull of 8 spheres)"""
    pts=[_sp(r,(x,y,z)) for x in(x0+r,x1-r) for y in(y0+r,y1-r) for z in(z0+r,z1-r)]
    return Manifold.batch_hull(pts)
def rtaper(secA,secB,r=3.0):
    """rounded loft between two rectangular sections, each (x0,x1,y0,y1,z0,z1)"""
    pts=[]
    for (x0,x1,y0,y1,z0,z1) in (secA,secB):
        pts+=[_sp(r,(x,y,z)) for x in(x0+r,x1-r) for y in(y0+r,y1-r) for z in(z0+r,z1-r)]
    return Manifold.batch_hull(pts)
def cyl_z(h,r,c=(0,0,0)): return Manifold.cylinder(h,r,r,SEG,True).translate(list(c))
def cyl_x(h,r,c=(0,0,0)): return Manifold.cylinder(h,r,r,48,True).rotate([0,90,0]).translate(list(c))
def slot_x(y,z,d,length,x_c,depth):
    return cyl_x(depth,d/2,(x_c,y,z-length/2))+cyl_x(depth,d/2,(x_c,y,z+length/2))+cube(depth,d,length,(x_c,y,z))

def cable_clip(x_face, y_c, z_c, length=10.0, open_dir=1):
    """snap-in cable clip standing on a plate face at x=x_face; bore axis along Z; slit opens toward +/-Y."""
    ro=CLIP_D_IN/2+CLIP_WALL; xc=x_face+ro-0.5
    c=cyl_z(length,ro,(xc,y_c,z_c))-cyl_z(length+2,CLIP_D_IN/2,(xc,y_c,z_c))
    c-=box(xc-CLIP_SLIT/2,xc+CLIP_SLIT/2,y_c-open_dir*ro-1,y_c+open_dir*ro+1,z_c-length/2-1,z_c+length/2+1) if False else box(xc-0.5*CLIP_SLIT,xc+0.5*CLIP_SLIT,min(y_c,y_c+open_dir*(ro+1)),max(y_c,y_c+open_dir*(ro+1)),z_c-length/2-1,z_c+length/2+1)
    base=box(x_face-1.0,x_face+1.5,y_c-ro,y_c+ro,z_c-length/2,z_c+length/2)
    return c+base

def zip_slot_x(y,z,x0,x1):
    """through slot along X for a zip tie that wraps a cable on the other side (tie width along Z)"""
    return box(x0,x1,y-ZIP_T/2,y+ZIP_T/2,z-ZIP_W/2,z+ZIP_W/2)

def cuff(circ, length, zc, z_top, z_bot):
    """C-cuff around Z at centre zc, lateral plate spanning z_bot..z_top."""
    r_in=circ/(2*math.pi)+CLEAR; r_out=r_in+WALL; px=r_out+PLATE_T
    body=cyl_z(length,r_out,(0,0,zc))
    body+=box(r_out-14,px,-PLATE_W/2,PLATE_W/2,z_bot,z_top)
    body-=cyl_z(abs(z_top-z_bot)+length+200,r_in,(0,0,zc))
    xcut=r_out*math.cos(math.radians(ARC_HALF))
    body-=box(-(r_out+6),xcut,-(r_out+6),(r_out+6),zc-length/2-1,zc+length/2+1)   # keep only the saddle
    r_mid=r_in+WALL/2
    for dz in (-length*.26,length*.26):
        for s in (-1,1):
            a=s*(ARC_HALF-14)
            body-=cube(WALL*3,3.5,STRAP_W,(r_mid*math.cos(math.radians(a)),r_mid*math.sin(math.radians(a)),zc+dz)).rotate([0,0,0]) if False else cube(WALL*3,3.5,STRAP_W,(0,0,0)).rotate([0,0,a]).translate([r_mid*math.cos(math.radians(a)),r_mid*math.sin(math.radians(a)),zc+dz])
    return body,r_in,r_out,px

def revolve_poly(pts,a0,a1,seg=96):
    """revolve an (r,z) polygon about the world Z axis from angle a0 to a1 (deg, from +X toward +Y)"""
    cs=CrossSection([[list(p) for p in pts]],FillRule.NonZero)
    m=Manifold.revolve(cs,seg,a1-a0)
    return m.rotate([0,0,a0])

def roll_rail():
    rc=ROLL_RC; z0=ROLL_Z0; z1=z0+RAIL_STEM_H; z2=z1+RAIL_HEAD_H
    pts=[(rc-RAIL_STEM,z0),(rc+RAIL_STEM,z0),(rc+RAIL_STEM,z1),(rc+RAIL_HEAD,z1),(rc+RAIL_HEAD,z2),(rc-RAIL_HEAD,z2),(rc-RAIL_HEAD,z1),(rc-RAIL_STEM,z1)]
    r=revolve_poly(pts,-ROLL_HALF,ROLL_HALF)
    for a in ROLL_SCREW_ANG:
        x=rc*math.cos(math.radians(a)); y=rc*math.sin(math.radians(a))
        r-=cyl_z(RAIL_STEM_H+RAIL_HEAD_H+2,ROLL_SCREW_D/2,(x,y,(z0+z2)/2))
        r-=cyl_z(4.0,4.2,(x,y,z2-1.0))                       # counterbore: screw head sits below the head's top face
    return r

def roll_slot():
    """the curved T-slot, to be subtracted from the strut foot"""
    rc=ROLL_RC; z0=ROLL_Z0; z1=z0+RAIL_STEM_H; z2=z1+RAIL_HEAD_H; c=SLIDE_CLR
    pts=[(rc-RAIL_STEM-c,z0-3),(rc+RAIL_STEM+c,z0-3),(rc+RAIL_STEM+c,z1-c),(rc+RAIL_HEAD+c,z1-c),(rc+RAIL_HEAD+c,z2+c),(rc-RAIL_HEAD-c,z2+c),(rc-RAIL_HEAD-c,z1-c),(rc-RAIL_STEM-c,z1-c)]
    return revolve_poly(pts,-55.0,55.0)

def upper_cuff():
    zc=GAP_UP+UPPER_CUFF_LEN/2
    z_lo=-SV_SHAFT_END-SV_CLEAR-CRADLE_WALL-4
    body,r_in,r_out,px=cuff(UPPER_ARM_CIRC,UPPER_CUFF_LEN,zc,GAP_UP+UPPER_CUFF_LEN,z_lo)
    py=SV_W+2*SV_CLEAR; pz=SV_L+2*SV_CLEAR
    z0=-SV_SHAFT_END-SV_CLEAR; z1=SV_L-SV_SHAFT_END+SV_CLEAR
    cradle=box(px,px+CRADLE_H,-(py/2+CRADLE_WALL),py/2+CRADLE_WALL,z0-CRADLE_WALL,z1+CRADLE_WALL)
    cradle-=box(px-0.01,px+CRADLE_H+1,-py/2,py/2,z0,z1)       # pocket open toward +X
    # servo ear screw bosses: the servo's end flanges sit on top of the end walls and screw straight down (-X) into them
    zm_=(z0+z1)/2
    for sz in(-1,1):
        zin=zm_+sz*(z1-z0)/2                                  # inner face of this end wall
        zout=zm_+sz*(EAR_Z/2+6.0)                             # pad reaches 6 mm past the hole centre
        cradle+=rbox(px,px+CRADLE_H,-(EAR_Y+9.0),EAR_Y+9.0,min(zin,zout),max(zin,zout),2.0)
    cradle-=box(px-0.01,px+CRADLE_H+1,-py/2,py/2,z0,z1)       # keep the pocket clear
    for sy in(-1,1):
        for sz in(-1,1):                                      # 4 blind pilot holes from the top face of the end walls
            xc_=px+CRADLE_H-EAR_PILOT_DEPTH/2+0.01
            for dz in(-EAR_SLOT/2+EAR_PILOT_D/2,EAR_SLOT/2-EAR_PILOT_D/2):   # two overlapping pilots = a short slot along Z
                cradle-=cyl_x(EAR_PILOT_DEPTH+0.01,EAR_PILOT_D/2,(xc_,sy*EAR_Y,zm_+sz*EAR_Z/2+dz))
    # servo lead exit: notch through the +Z end wall at floor level (PLACEHOLDER side, see LEAD_*)
    cradle-=box(px-0.01,px+LEAD_NOTCH_H,-LEAD_NOTCH_W/2,LEAD_NOTCH_W/2,z1-0.5,z1+CRADLE_WALL+EAR_SLOT)
    body+=cradle
    zm=(z0+z1)/2
    for sy in(-1,1):
        for sz in(-1,1):                                       # ear-bolt slots (placeholder)
            body-=slot_x(sy*EAR_Y,zm+sz*EAR_Z/2,3.4,10,px-3,20)
    body-=cyl_x(PLATE_T+30,9.0,(px-3,0,0))                     # shaft clearance
    # ---- end stops, integral with the cradle (they carry the servo's stall torque) ----
    x0=px+0.0; x1=px+48.0
    zc_bot=z0-CRADLE_WALL                                      # bottom end of cradle
    if PRIMARY:
        # extension post: rounded, tapering toward its tip; contact face stays at y=EXT_POST_Y
        body+=rtaper((x0,x1,EXT_POST_Y-20.0,EXT_POST_Y,-48.0,zc_bot+3),(x0+8,x1-12,EXT_POST_Y-12.0,EXT_POST_Y,-76.0,-70.0),3.0)
        # flexion stop: rounded horn, broad where it joins the cradle, narrower at its striking face (y=FLEX_BLOCK_Y)
        yb=py/2+CRADLE_WALL-3.0
        body+=rtaper((x0,x1,yb,yb+4.0,FLEX_BLOCK_Z[0],FLEX_BLOCK_Z[1]),(x0,x1-4.0,FLEX_BLOCK_Y-14.0,FLEX_BLOCK_Y,FLEX_BLOCK_Z[0]+12.0,FLEX_BLOCK_Z[1]-12.0),4.0)
    # ---- backup stops on the saddle plate itself (same x-slab as the forearm saddle plate) ----
    xs0=r_out-14.0
    if BACKUP:
        body+=rbox(xs0,px,-PLATE_W/2,-PLATE_W/2+9.0,EXT2_TAB_Z,z_lo+3.0,2.5)        # backup extension stop (hangs down, -Y edge)
        body+=rbox(xs0,px,PLATE_W/2-3.0,FLEX2_Y,FLEX2_Z[0],FLEX2_Z[1],2.5)           # backup flexion stop (+Y edge)
    # roll-rail mounting: 3 blind pilot holes (M4 self-tapping; use 5.6 mm for heat-set inserts) in the top face of the saddle plate
    for a in ROLL_SCREW_ANG:
        body-=cyl_z(ROLL_PILOT_DEPTH+0.02,ROLL_PILOT_D/2,(ROLL_RC*math.cos(math.radians(a)),ROLL_RC*math.sin(math.radians(a)),ROLL_Z0-ROLL_PILOT_DEPTH/2+0.01))
    # cable clips on the saddle plate, between the cradle and the rail, off the strut's y-range (lead runs +Z toward the shoulder)
    for zc_ in (95.0,118.0): body+=cable_clip(px,PLATE_W/2-8.0,zc_,10.0,1)
    return body,px,r_out

def forearm_cuff(px_u):
    zc=-(GAP_DN+FOREARM_CUFF_LEN/2)
    z_top=-GAP_DN; z_bot=zc-FOREARM_CUFF_LEN/2-RAIL_LEN
    body,r_in,r_out,px=cuff(FOREARM_CIRC,FOREARM_CUFF_LEN,zc,z_top,min(z_bot,WRIST_Z-16.0))
    link_x0=px_u+SV_H+HORN_STACK
    for sy in(-1,1):                                            # fins carry the elbow torque
        y0=sy*FIN_Y-FIN_T/2; y1=sy*FIN_Y+FIN_T/2
        fin=box(px-4,link_x0,min(y0,y1),max(y0,y1),BOLT_Z[1]-12,BOLT_Z[0]+12)
        for bz in BOLT_Z:
            fin-=cyl_x(14,2.1,(link_x0-7,sy*FIN_Y,bz))          # M4 heat-set pilot
        body+=fin
    for sy in(-1,1):                                            # rail slots for optional wrist mount
        for rz in(z_bot+25,z_bot+70):
            body-=slot_x(sy*14,rz,4.5,8,px-3,24)
    # ---- wrist pivot ear: a solid block reaching out to the crank/rod layers; the hand piece pivots at its end ----
    xe=wrist_layers(px)["ear_end"]
    body+=box(px-1,xe,-22.0,22.0,WRIST_Z-16.0,WRIST_Z+16.0)
    body-=cyl_x(xe-px+6,(PIN_D+0.4)/2,((px+xe)/2,0.0,WRIST_Z))          # pivot pin hole
    body-=cyl_x(xe-px+6,(PIN_D+0.4)/2,((px+xe)/2,BOLT_Y,WRIST_Z))       # wrist-stop bolt hole
    return body,px,r_out,link_x0


# ---------------- STRAIGHT-BAR FOREARM (alternative to the curved saddle; same interface to link plate, stops, wrist) ----
BAR_W, BAR_T   = 36.0, 8.0            # bar width (Y) and thickness (X); 36 wide so the wrist-mount rail slots (y=+-14) fit
BAR_STRAPS_Z   = (-85.0, -130.0)      # Velcro strap slots (strap passes through the bar, around the forearm)

def forearm_bar(px_u):
    """Flat straight bar down the outer side of the forearm. Strap slots take Velcro straps that wrap the arm.
    Same x-position (plate face px) and torque fins as the curved saddle, so every other part fits unchanged."""
    r_in=FOREARM_CIRC/(2*math.pi)+CLEAR; r_out=r_in+WALL; px=r_out+PLATE_T
    link_x0=px_u+SV_H+HORN_STACK
    z_top=-GAP_DN+10.0; z_bot_bar=WRIST_Z-16.0
    body=rbox(px-BAR_T,px,-BAR_W/2,BAR_W/2,z_bot_bar,z_top,4.0)
    for sy in(-1,1):                                            # same torque fins as the saddle
        y0=sy*FIN_Y-FIN_T/2; y1=sy*FIN_Y+FIN_T/2
        fin=box(px-4,link_x0,min(y0,y1),max(y0,y1),BOLT_Z[1]-12,BOLT_Z[0]+12)
        for bz in BOLT_Z:
            fin-=cyl_x(14,2.1,(link_x0-7,sy*FIN_Y,bz))
        body+=fin
    for zc in BAR_STRAPS_Z:                                     # strap slots: long side along Y, 3.5 thick along Z
        body-=box(px-BAR_T-1,px+1,-STRAP_W/2-0.5,STRAP_W/2+0.5,zc-1.9,zc+1.9)
    z_bot=-(GAP_DN+FOREARM_CUFF_LEN)-RAIL_LEN
    for sy in(-1,1):                                            # rail slots for optional wrist mount (same as saddle)
        for rz in(z_bot+25,z_bot+70):
            body-=slot_x(sy*14,rz,4.5,8,px-3,24)
    xe=wrist_layers(px)["ear_end"]
    body+=box(px-1,xe,-22.0,22.0,WRIST_Z-16.0,WRIST_Z+16.0)
    body-=cyl_x(xe-px+6,(PIN_D+0.4)/2,((px+xe)/2,0.0,WRIST_Z))
    body-=cyl_x(xe-px+6,(PIN_D+0.4)/2,((px+xe)/2,BOLT_Y,WRIST_Z))
    for zz in (-60.0,-105.0,-160.0,-200.0):                     # zip-tie pairs straddling the lead that rides on the bar's outer face
        for sy in(-1,1): body-=zip_slot_x(sy*5.2,zz,px-BAR_T-1,px+1)
    return body,px,r_out,link_x0

def link_plate(link_x0):
    L_top=16.0; L_bot=BOLT_Z[1]-12
    p=box(link_x0,link_x0+LINK_T,-LINK_W/2,LINK_W/2,L_bot,L_top)
    p-=cyl_x(LINK_T+2,4.0,(link_x0+LINK_T/2,0,0))               # horn screw
    for a in(0,90,180,270):                                      # PLACEHOLDER horn pattern
        p-=cyl_x(LINK_T+2,1.7,(link_x0+LINK_T/2,11*math.sin(math.radians(a)),11*math.cos(math.radians(a))))
    for sy in(-1,1):
        for bz in BOLT_Z: p-=cyl_x(LINK_T+2,2.2,(link_x0+LINK_T/2,sy*FIN_Y,bz))
    return p

def servo_ph(px):
    z0=-SV_SHAFT_END
    b=box(px,px+SV_H,-SV_W/2,SV_W/2,z0,z0+SV_L)
    return b+cyl_x(4,10,(px+SV_H+2,0,0))

def wrist_layers(px_f):
    """x positions of the stacked wrist layers (all measured outward from the forearm plate face px_f)."""
    horn=px_f+6+WS_H+4.0
    return dict(horn=horn,crank=(horn,horn+4),rod=(horn+4,horn+8),side=(horn+8,horn+12),ear_end=horn+3.0)

def wrist_mount(px_f):
    """OPTIONAL: bolts on the forearm rail, holds the wrist servo. Local origin = servo shaft; servo shaft points +X."""
    base=box(px_f,px_f+6,-PLATE_W/2,PLATE_W/2,-45,45)
    for sy in(-1,1):
        for rz in(-22.5,22.5): base-=slot_x(sy*14,rz,4.5,8,px_f+3,12)
    py=WS_W+2*SV_CLEAR
    z0=-WS_SHAFT_END-SV_CLEAR; z1=WS_L-WS_SHAFT_END+SV_CLEAR
    wall=box(px_f+6,px_f+6+WS_H-12,-(py/2+4),py/2+4,z0-4,z1+4)
    wall-=box(px_f+5.99,px_f+6+WS_H,-py/2,py/2,z0,z1)
    wall-=box(px_f+5.99,px_f+6+LEAD_NOTCH_H,-LEAD_NOTCH_W/2,LEAD_NOTCH_W/2,z1-0.5,z1+5.0)   # lead exit notch (PLACEHOLDER side)
    return base+wall

def wrist_servo_ph(px_f):
    z0=-WS_SHAFT_END
    b=box(px_f+6,px_f+6+WS_H,-WS_W/2,WS_W/2,z0,z0+WS_L)
    return b+cyl_x(6,6,(px_f+6+WS_H+3,0,0))

def hand_piece(px_f):
    """OPTIONAL: dorsal hand plate + lateral side plate. Local origin = wrist pivot P (so place it at z=WRIST_Z)."""
    L=wrist_layers(px_f); x0,x1=L["side"]
    yp=HAND_T/2+DORSAL_FOAM
    zlo=-(0.52*HAND_LEN); zhi=-28.0
    # dorsal plate follows the back of the hand: narrower at the wrist end, wider across the knuckles, all edges rounded
    plate=rtaper((-(HAND_W/2-6),(HAND_W/2-6),yp,yp+4,zhi-12.0,zhi),(-(HAND_W/2+2),(HAND_W/2+2),yp,yp+4,zlo,zlo+12.0),1.9)
    wing=rbox(HAND_W/2-8,x1,yp,yp+4,-56.0,zhi,1.9)
    side=box(x0,x1,-26.0,34.0,-50.0,22.0)
    body=plate+wing+side
    body-=cyl_x(x1-x0+4,(PIN_D+0.4)/2,((x0+x1)/2,0.0,0.0))             # pivot
    body-=cyl_x(x1-x0+4,1.7,((x0+x1)/2,LEVER_A,0.0))                   # rod pin A
    for k in range(-int(LIM_FLEX),int(LIM_EXT)+1,2):                     # arc slot = the wrist stops
        a=math.radians(k)
        body-=cyl_x(x1-x0+4,(PIN_D+0.8)/2,((x0+x1)/2,-ARC_R*math.cos(a),ARC_R*math.sin(a)))
    for sx in(-1,1):
        for z in(-48.0,-82.0): body-=cube(3.5,8.0,25.5,(sx*(HAND_W/2-16),yp+2,z))   # strap slots (inside the plate outline)
    return body

def bar(length,w=12.0,t=4.0,holes=(0.0,),hd=3.4):
    """flat link along +Y from y=0; used for crank and rod. thickness along X from 0."""
    b=box(0,t,-w/2,length+w/2,-w/2,w/2)
    b-=cyl_x(0,0,(0,0,0)) if False else box(0,0,0,0,0,0)
    return b

def link_bar2(length,hole_ys,hd=3.4,w=12.0,t=4.0,extra=()):
    b=box(0,t,-w/2,length+w/2,-w/2,w/2)
    for y in hole_ys: b-=cyl_x(t+2,hd/2,(t/2,y,0))
    for y,d in extra: b-=cyl_x(t+2,d/2,(t/2,y,0))
    return b

def crank_part():   return link_bar2(RC,(RC,),extra=((0.0,4.0),(8.0,2.2),(-8.0,2.2)),w=14.0)
def rod_part():     return link_bar2(ROD,(0.0,ROD))

def kinematics():
    """planar (y,z) solution: wrist angle phi -> crank angle. Returns table and pose function."""
    P=np.array([0.0,WRIST_Z]); zb=-(GAP_DN+FOREARM_CUFF_LEN/2)-FOREARM_CUFF_LEN/2-RAIL_LEN
    S=np.array([0.0,zb+47.5])
    def A(phi):
        a=math.radians(phi); return P+LEVER_A*np.array([math.cos(a),math.sin(a)])
    def solve(phi,prev=None):
        a=A(phi); d=np.linalg.norm(a-S)
        if d>RC+ROD or d<abs(ROD-RC): return None
        base=math.atan2(a[1]-S[1],a[0]-S[0]); psi=math.acos((RC**2+d**2-ROD**2)/(2*RC*d))
        cands=[base+psi,base-psi]
        if prev is None: cands.sort(key=lambda c:abs((c-base-math.radians(60)+math.pi)%(2*math.pi)-math.pi))
        else: cands.sort(key=lambda c:abs((c-prev+math.pi)%(2*math.pi)-math.pi))
        return cands[0]
    return P,S,A,solve

def save(m,name):
    me=m.to_mesh()
    tm=trimesh.Trimesh(np.asarray(me.vert_properties)[:,:3],np.asarray(me.tri_verts),process=True)
    tm.export(os.path.join(OUT,name))
    print(f"{name:42s} watertight={tm.is_watertight} bbox={np.round(tm.extents,1)}")

def chest_plate():
    r_in=CHEST_CIRC/(2*math.pi)+CHEST_FOAM; r_out=r_in+CHEST_T
    H=CHEST_H
    shell=cyl_z(H,r_out,(0,0,H/2))-cyl_z(H+2,r_in,(0,0,H/2))
    shell=shell^box(-CHEST_W/2,CHEST_W/2,0,r_out+10,0,H)         # keep the front arc only
    # flat pad for the tray, filling the gap between the curved surface and a flat plane
    y_edge=math.sqrt(r_out**2-PAD_X**2)
    pad=box(-PAD_X,PAD_X,y_edge-3,r_out+4,PAD_Z[0],PAD_Z[1])
    zc=(PAD_Z[0]+PAD_Z[1])/2
    for sx in(-1,1):
        for sz in(-1,1):                                           # blind heat-set pilots, do not break through to skin
            h=Manifold.cylinder(10,2.1,2.1,32,False).rotate([-90,0,0]).translate([sx*PATTERN[0]/2,r_out+4-10,zc+sz*PATTERN[1]/2])
            pad-=h
    body=shell+pad
    # strap slots: shoulder straps (top, strap runs vertically) and torso wrap straps (ends, strap runs horizontally)
    r_mid=(r_in+r_out)/2
    def slot(phi,z,tang,vert):
        a=math.radians(phi); c=(r_mid*math.sin(a),r_mid*math.cos(a),z)
        return cube(14,tang,vert,(0,0,0)).rotate([0,0,90-phi]).translate(list(c))
    for ph in(-18,18): body-=slot(ph,H-14,25.5,3.5)               # shoulder straps
    half=math.degrees(math.asin((CHEST_W/2)/r_out))
    for sgn in(-1,1):
        for z in(40,110): body-=slot(sgn*(half-9),z,3.5,25.5)       # torso straps
    for xx in (79.0,62.0):                                          # zip-tie pairs straddling the lead below the yoke foot, running inboard toward the tray
        ph_=math.degrees(math.asin(xx/r_mid))
        for dz in(-5.2,5.2): body-=cube(14,ZIP_W,ZIP_T,(0,0,0)).rotate([0,0,90-ph_]).translate([r_mid*math.sin(math.radians(ph_)),r_mid*math.cos(math.radians(ph_)),46.0+dz])
    body-=chest_foot_holes_for_plate()                              # 4 x M4 holes for the shoulder-yoke foot (right end)
    return body,r_out

def tray_parts():
    L,W,Hh=TRAY_IN; o=TRAY_WALL
    tray=box(-L/2-o,L/2+o,-W/2-o,W/2+o,0,TRAY_FLOOR+Hh)-box(-L/2,L/2,-W/2,W/2,TRAY_FLOOR,TRAY_FLOOR+Hh+1)
    for sx in(-1,1):
        for sy in(-1,1):
            tray-=Manifold.cylinder(TRAY_FLOOR+2,1.7,1.7,24,False).translate([sx*PATTERN[0]/2,sy*PATTERN[1]/2,-1])  # screw to pad
            tray+=Manifold.cylinder(Hh,3.2,3.2,24,False).translate([sx*(L/2-4),sy*(W/2-4),TRAY_FLOOR])               # lid posts
            tray-=Manifold.cylinder(Hh-2,1.2,1.2,24,False).translate([sx*(L/2-4),sy*(W/2-4),TRAY_FLOOR+2])
    tray-=box(L/2-1,L/2+o+1,-10,10,TRAY_FLOOR+6,TRAY_FLOOR+Hh-6)     # cable exit on the RIGHT end (+X)
    lid=box(-L/2-o,L/2+o,-W/2-o,W/2+o,0,3)
    for sx in(-1,1):
        for sy in(-1,1): lid-=Manifold.cylinder(5,1.7,1.7,24,False).translate([sx*(L/2-4),sy*(W/2-4),-1])
    lid-=Manifold.cylinder(5,ESTOP_D/2,ESTOP_D/2,48,False).translate([-L/2+22,0,-1])   # e-stop on the LEFT end (-X)
    return tray,lid


def _radial_cyl(h,r,phi_deg,t,z,r_c):
    """cylinder along the local radial direction (plate frame, phi from +Y toward +X), centre at radius r_c, tangential offset t"""
    a=math.radians(phi_deg)
    c=(r_c*math.sin(a)+t*math.cos(a), r_c*math.cos(a)-t*math.sin(a), z)
    return Manifold.cylinder(h,r,r,32,True).rotate([-90,0,0]).rotate([0,0,-phi_deg]).translate(list(c))

def chest_foot_geometry():
    """foot position on the chest plate: returns (phi_deg, r_out)"""
    r_out=CHEST_CIRC/(2*math.pi)+CHEST_FOAM+CHEST_T
    return math.degrees(math.asin(FOOT_PHI_X/r_out)), r_out

def chest_foot_holes_for_plate():
    """through holes in the chest plate for the foot bolts (4 x M4, heads on the skin side)"""
    phi,r_out=chest_foot_geometry(); r_in=r_out-CHEST_T
    cut=None
    for t in(-FOOT_HOLES,FOOT_HOLES):
        for dz in(-FOOT_HOLES,FOOT_HOLES):
            c=_radial_cyl(CHEST_T+8,STRUT_BOLT_D/2,phi,t,FOOT_Z+dz,(r_in+r_out)/2)
            cut=c if cut is None else cut+c
    return cut

def yoke_waypoints():
    """arch centre-line in the ELBOW frame: chest foot -> over the shoulder -> gimbal ears"""
    phi,r_out=chest_foot_geometry(); a=math.radians(phi); r=r_out+10.0
    foot=(CHEST_AXIS_X+r*math.sin(a), r*math.cos(a), CHEST_PLATE_Z0+FOOT_Z)
    zs=UPPER_ARM_LEN
    bx=STRUT_BX-STRUT_T+BLOCK[0]/2
    return [foot,(foot[0],foot[1],foot[2]+60),(CHEST_AXIS_X+105.0,60.0,zs+45.0),(-30.0,10.0,zs+70.0),(40.0,0.0,zs+72.0),(bx,0.0,zs+62.0),(bx,0.0,zs+52.0)]

def _capsule(p,q,r):
    return Manifold.batch_hull([_sp(r,p),_sp(r,q)])

def chest_link(px_u):
    """returns dict of parts in the ELBOW frame"""
    global STRUT_BX
    STRUT_BX=px_u+STRUT_T+STRUT_T          # block starts one strut-thickness beyond the strut's outer face
    zs=UPPER_ARM_LEN
    # ---- shoulder strut (bolts to the upper saddle plate, pivots on the gimbal block about X) ----
    # wide (36 mm) lower section so the M4 holes at y=+-14 stay fully enclosed; narrower (32 mm) top clears the yoke ears
    # upright (32 mm wide) from the carriage foot up to the shoulder bolt; the foot carries the curved T-slot that rides on the roll rail
    st=rbox(px_u,px_u+STRUT_T,-STRUT_W/2,STRUT_W/2,CARR_ZTOP-6.0,zs+16.0,4.0)
    carriage=rbox(CARR_X0,px_u+STRUT_T,-CARR_Y,CARR_Y,ROLL_Z0+1.0,CARR_ZTOP,3.0)
    st=st+carriage
    st-=roll_slot()
    for zz in (190.0,240.0):                                       # zip-tie pairs: the lead rides on the strut's outer face
        for sy in(-1,1): st-=zip_slot_x(sy*5.2,zz,px_u-1,px_u+STRUT_T+1)
    st-=cyl_x(STRUT_T+2,2.75,(px_u+STRUT_T/2,0.0,zs))            # shoulder bolt M5 clearance
    st-=cyl_x(3.0,4.6,(px_u+1.0,0.0,zs))                         # head counterbore, saddle side
    # ---- gimbal block: X-axis hole (blind, insert) toward the strut, Y-axis hole through for the yoke pin ----
    bx0=STRUT_BX-STRUT_T
    bk=rbox(bx0,bx0+BLOCK[0],-BLOCK[1]/2,BLOCK[1]/2,zs-14.0,zs+36.0,3.0)
    bk-=cyl_x(18.0,2.8,(bx0+9.0-0.01,0.0,zs))
    bk-=Manifold.cylinder(BLOCK[1]+4,2.7,2.7,32,True).rotate([90,0,0]).translate([bx0+BLOCK[0]/2,0.0,zs+22.0])
    # ---- arch yoke: capsule bar from foot to ears, plus foot plate and two clevis ears ----
    wp=yoke_waypoints()
    arch=None
    for p,q in zip(wp[:-1],wp[1:]):
        c=_capsule(p,q,8.0); arch=c if arch is None else arch+c
    phi,r_out=chest_foot_geometry()
    foot_l=(cyl_z(CHEST_H+200,r_out+12,(0,0,0))-cyl_z(CHEST_H+400,r_out,(0,0,0)))
    foot_l=foot_l^box(FOOT_PHI_X-20,FOOT_PHI_X+20,1,r_out+20,FOOT_Z-20,FOOT_Z+20)
    foot_l=foot_l.translate([CHEST_AXIS_X,0,CHEST_PLATE_Z0])
    for t in(-FOOT_HOLES,FOOT_HOLES):
        for dz in(-FOOT_HOLES,FOOT_HOLES):
            foot_l-=_radial_cyl(14.0,STRUT_INSERT_D/2,phi,t,FOOT_Z+dz,r_out+7.0).translate([CHEST_AXIS_X,0,CHEST_PLATE_Z0])
    arch+=foot_l
    bxc=bx0+BLOCK[0]/2
    for sy in(-1,1):
        yc=sy*(BLOCK[1]/2+0.6+3.0)
        arch+=rbox(bxc-14.0,bxc+14.0,yc-3.0,yc+3.0,zs+6.0,zs+60.0,3.0)
    arch-=Manifold.cylinder(60,2.7,2.7,32,True).rotate([90,0,0]).translate([bxc,0.0,zs+22.0])
    return dict(strut=st,block=bk,yoke=arch,xform=(bxc,zs))

def body_reference(px_u):
    """simple torso + arm + shoulder reference (NOT printable), elbow frame"""
    r_t=CHEST_CIRC/(2*math.pi)
    torso=cyl_z(420,r_t,(CHEST_AXIS_X,0,CHEST_PLATE_Z0+60))
    arm=cyl_z(UPPER_ARM_LEN,UPPER_ARM_CIRC/(2*math.pi),(0,0,UPPER_ARM_LEN/2))
    fore=cyl_z(FOREARM_LEN,FOREARM_CIRC/(2*math.pi),(0,0,-FOREARM_LEN/2))
    shoulder=Manifold.sphere(52,32).translate([0,0,UPPER_ARM_LEN])
    return torso,arm+fore+shoulder

S_Z=-(GAP_DN+FOREARM_CUFF_LEN/2)-FOREARM_CUFF_LEN/2-RAIL_LEN+47.5
if __name__=="__main__":
    up,px_u,ro_u=upper_cuff()
    fa,px_f,ro_f,lx0=forearm_cuff(px_u)
    lk=link_plate(lx0); sv=servo_ph(px_u); wm=wrist_mount(px_f).translate([0,0,S_Z])
    save(up,"01_upper_cuff_with_servo_cradle.stl")
    save(fa,"02_forearm_cuff_with_torque_fins_and_wrist_rail.stl")
    save(lk,"03_link_plate_DS51150.stl")
    save(wm,"04_OPTIONAL_wrist_servo_mount.stl")
    save(sv,"05_DS51150_PLACEHOLDER_not_printable.stl")
    # reference assembly (arm straight)
    asm=up+sv+lk+fa
    save(asm,"00_assembly_arm_straight_REFERENCE.stl")
    # ---- safety geometry check: free travel between the stops, contact exactly at the stops ----
    fixed=up+sv; moving=fa+lk
    cp,r_out_c=chest_plate(); tr,ld=tray_parts()
    save(cp,"06_chest_plate_RIGHT_ARM.stl"); save(tr,"07_electronics_tray.stl"); save(ld,"08_tray_lid_with_estop_hole.stl")
    def hit(d): return (fixed^moving.rotate([d,0,0])).volume()>0.5
    free=[d for d in range(0,int(FLEX_LIMIT_DEG)) if hit(d)]
    print("\nangles with contact inside the free range 0..%d deg: %s"%(int(FLEX_LIMIT_DEG)-1, free if free else "none"))
    ext=next((d for d in range(0,-20,-1) if hit(d)),None)
    flex=next((d for d in range(60,141) if hit(d)),None)
    print("PRIMARY stops (cradle): extension ~%s deg, flexion ~%s deg"%(ext,flex))
    PRIMARY=False
    up2,_,_=upper_cuff(); PRIMARY=True
    fixed2=up2+sv
    def hit2(d): return (fixed2^moving.rotate([d,0,0])).volume()>0.5
    print("BACKUP stops alone (saddle plates): extension ~%s deg, flexion ~%s deg"%(next((d for d in range(0,-20,-1) if hit2(d)),None),next((d for d in range(60,141) if hit2(d)),None)))

    # ================= WRIST MODULE =================
    L=wrist_layers(px_f)
    hp=hand_piece(px_f); cr=crank_part(); rd=rod_part()
    save(hp,"09_OPTIONAL_hand_piece_dorsal_plate.stl")
    save(cr,"10_OPTIONAL_wrist_crank.stl"); save(rd,"11_OPTIONAL_wrist_rod.stl")
    wsv=wrist_servo_ph(px_f).translate([0,0,S_Z])
    save(wsv,"12_WRIST_SERVO_PLACEHOLDER_not_printable.stl")
    P,S,A,solve=kinematics()
    def pose(phi,al):
        """returns (hand, crank, rod) in world for wrist angle phi (deg) and crank angle al (rad)"""
        hand=hp.translate([0,0,0]).rotate([phi,0,0]).translate([0,0,WRIST_Z])
        c=cr.rotate([math.degrees(al),0,0]).translate([L["crank"][0],S[0],S[1]])
        C=S+RC*np.array([math.cos(al),math.sin(al)]); a=A(phi); d=a-C
        ang=math.degrees(math.atan2(d[1],d[0]))
        r=rd.rotate([ang,0,0]).translate([L["rod"][0],C[0],C[1]])
        return hand,c,r
    wfixed=fa+wm
    prev=None; bad=[]
    for phi in range(-int(LIM_FLEX),int(LIM_EXT)+1,5):
        al=solve(phi,prev); prev=al
        h,c,r=pose(phi,al)
        for nm,mv in(("hand",h),("crank",c),("rod",r)):
            v=(wfixed^mv).volume()
            if v>0.5: bad.append((phi,nm,round(v,1)))
        v=(h^c).volume()+(h^r).volume()+(c^r).volume()
        if v>0.5: bad.append((phi,"moving-moving",round(v,1)))
    print("\nwrist sweep collisions:",bad if bad else "none")
    ph0=0.0; al0=solve(0.0,None)
    h,c,r=pose(0.0,al0)
    save(up+sv+lk+fa+wm+wsv+h+c+r,"13_assembly_with_wrist_REFERENCE.stl")

    # ================= STRAIGHT-BAR FOREARM VARIANT =================
    fb,pxb,_,lxb=forearm_bar(px_u); lkb=link_plate(lxb)
    save(fb,"02B_forearm_straight_bar_with_torque_fins.stl")
    save(up+sv+lkb+fb,"00B_assembly_straight_bar_REFERENCE.stl")
    mvb=fb+lkb
    hitb=lambda d:((up+sv)^mvb.rotate([d,0,0])).volume()>0.5
    print("\nBAR variant: contact inside free range 0..%d:"%(int(FLEX_LIMIT_DEG)-1),[d for d in range(0,int(FLEX_LIMIT_DEG)) if hitb(d)] or "none",
          "| extension ~%s, flexion ~%s"%(next((d for d in range(0,-20,-1) if hitb(d)),None),next((d for d in range(60,141) if hitb(d)),None)))
    wf=fb+wm; prev=None; badb=[]
    for phi in range(-int(LIM_FLEX),int(LIM_EXT)+1,5):
        al=solve(phi,prev); prev=al
        h,c,r=pose(phi,al)
        for nm,mvp in(("hand",h),("crank",c),("rod",r)):
            if (wf^mvp).volume()>0.5: badb.append((phi,nm))
    print("BAR variant wrist sweep collisions:",badb or "none")
    save(up+sv+lkb+fb+wm+wsv+pose(0.0,solve(0.0,None))[0]+pose(0.0,solve(0.0,None))[1]+pose(0.0,solve(0.0,None))[2],"13B_assembly_straight_bar_with_wrist_REFERENCE.stl")

    # ================= CHEST SUPPORT =================
    cl=chest_link(px_u)
    save(cl["strut"],"14_shoulder_strut.stl"); save(cl["block"],"15_gimbal_block.stl"); save(cl["yoke"],"16_chest_yoke_arch.stl")
    rail=roll_rail(); save(rail,"20_roll_rail.stl")
    # roll check: the arm module (saddle + servo + link + forearm + rail) rolls about the arm axis (world Z) while the strut/carriage stay fixed
    arm_all=up+sv+lk+fa+rail
    badr=[(a,round((arm_all.rotate([0,0,a])^cl["strut"]).volume(),1)) for a in range(-int(ROLL_HALF),int(ROLL_HALF)+1,4) if (arm_all.rotate([0,0,a])^cl["strut"]).volume()>0.5]
    print("\nROLL sweep (+-%d deg): arm module vs strut/carriage overlaps:"%ROLL_HALF, badr if badr else "none")
    print("  rail vs saddle (seat contact only):",round((rail^up).volume(),1),"| rail vs carriage at 0 deg:",round((rail^cl["strut"]).volume(),1))
    torso,limbs=body_reference(px_u)
    save(torso,"17_BODY_REFERENCE_torso_not_printable.stl"); save(limbs,"18_BODY_REFERENCE_arm_not_printable.stl")
    cpl,_r=chest_plate()
    cpl_arm=cpl.translate([CHEST_AXIS_X,0,CHEST_PLATE_Z0])
    asm_all=up+sv+lk+fa+rail+cl["strut"]+cl["block"]+cl["yoke"]+cpl_arm
    save(asm_all,"19_assembly_arm_plus_chest_support_REFERENCE.stl")
    # ---- checks: arch must not touch the arm/shoulder reference; strut/yoke must not collide except where intended ----
    print("\nCHEST SUPPORT checks (overlap volumes, mm^3):")
    print("  yoke vs arm+shoulder reference:",round((cl["yoke"]^limbs).volume(),1))
    print("  yoke vs strut:",round((cl["yoke"]^cl["strut"]).volume(),1)," yoke vs block (pin region only):",round((cl["yoke"]^cl["block"]).volume(),1))
    print("  strut vs upper saddle:",round((cl["strut"]^up).volume(),1)," block vs strut:",round((cl["block"]^cl["strut"]).volume(),1))
    print("  yoke vs chest plate (foot sits on it):",round((cl["yoke"]^cpl_arm).volume(),1))
    # swing test: strut+block+yoke are rigid; the arm may rotate about X at the shoulder. check the limbs sweeping +-60 deg about the shoulder X axis do not hit the yoke arch
    bad=[]
    for a in range(-40,121,10):
        l=limbs.translate([0,0,-UPPER_ARM_LEN]).rotate([a,0,0]).translate([0,0,UPPER_ARM_LEN])
        arm_only=(up+sv+lk+fa).translate([0,0,-UPPER_ARM_LEN]).rotate([a,0,0]).translate([0,0,UPPER_ARM_LEN])
        v=(arm_only^cl["yoke"]).volume()
        if v>0.5: bad.append((a,round(v,1)))
    print("  shoulder swing (-40..120 deg) arm module vs yoke, but only if strut were fixed:",bad or "none")
