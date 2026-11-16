#!/usr/bin/env python3
"""
Build the Aegis parts as FreeCAD documents (.FCStd), one per part, in cad/freecad/.

Same parts, same parameters and same frame as generator/make_aegis_v15.py (elbow axis = X through
the origin, +X = outer side of the RIGHT arm, +Z = toward the shoulder, +Y = forward). Millimetres.

Each .FCStd is a feature tree of Part workbench features (Box, Cylinder, Sphere, Polygon + Revolution,
Offset, Fuse, Cut, Common). Open a file in FreeCAD and edit any feature's size or placement in the
Property view; the booleans above it recompute. To change a global measurement (arm circumference,
servo size, chest size ...), edit the numbers below and run the script again.

The few "rounded taper" shapes are a fixed convex hull (Part::Feature "...Hull") rounded by a Part::Offset
whose radius can still be edited.

Run with FreeCAD's command-line interpreter (FreeCAD 1.0 or newer), from the repo root:
    freecadcmd -c "exec(open('generator/freecad/make_aegis_fcstd.py').read())"
Also writes a STEP file for every part to cad/freecad/step/ (real B-rep: cylinders are cylinders).
"""
import math, os
import FreeCAD as App, Part

V = App.Vector
_dp = App.ParamGet("User parameter:BaseApp/Preferences/Document")
_dp.SetBool("CreateBackupFiles", False); _dp.SetBool("SaveBinaryBrep", True); _dp.SetInt("CompressionLevel", 9)

# ---------------- arm (MEASURE) ----------------
UPPER_ARM_CIRC = 240.0
FOREARM_CIRC   = 220.0
CLEAR, WALL    = 3.0, 4.0
PLATE_T, PLATE_W = 8.0, 56.0
UPPER_CUFF_LEN, FOREARM_CUFF_LEN = 90.0, 80.0
ARC_HALF = 70.0
STRAP_W = 25.0
GAP_UP, GAP_DN = 40.0, 55.0
# ---------------- DS51150 (envelope from vendor page; mounting holes NOT confirmed) --------
SV_L, SV_W, SV_H = 65.0, 30.0, 48.0
SV_SHAFT_END   = 16.5
SV_CLEAR       = 0.8
CRADLE_WALL    = 5.0
CRADLE_H       = SV_H - 14.0
EAR_Y, EAR_Z   = 10.0, 75.0
EAR_PILOT_D    = 3.4
EAR_PILOT_DEPTH= 24.0
HORN_STACK     = 4.0
LINK_T, LINK_W = 8.0, 30.0
BOLT_Z         = (-55.0, -80.0)
FIN_T, FIN_Y   = 8.0, 11.0
# ---------------- optional wrist servo (MG996R-class envelope, PLACEHOLDER) --
FOREARM_LEN = 250.0
RAIL_LEN = FOREARM_LEN-15.0-(GAP_DN+FOREARM_CUFF_LEN)
# ---------------- chest plate + electronics tray ----------
CHEST_CIRC = 850.0
CHEST_FOAM = 10.0
CHEST_T    = 5.0
CHEST_W, CHEST_H = 200.0, 150.0
PAD_X, PAD_Z = 55.0, (35.0, 115.0)
PATTERN = (80.0, 40.0)
TRAY_IN = (110.0, 70.0, 35.0)
TRAY_WALL, TRAY_FLOOR = 3.0, 3.0
ESTOP_D = 22.3
# ---------------- hinged wrist module (OPTIONAL, not in the current build) ----
HAND_LEN, HAND_W, HAND_T = 195.0, 85.0, 30.0
DORSAL_FOAM = 5.0
WRIST_Z   = -FOREARM_LEN
LIM_FLEX, LIM_EXT = 55.0, 45.0
PIN_D, ARC_R = 5.0, 17.0
BOLT_Y = -17.0
LEVER_A = 28.0
RC, ROD = 30.0, 67.0
WS_L, WS_W, WS_H = 40.7, 19.7, 42.9
WS_SHAFT_END = 10.5
# ---------------- chest support ----------------
UPPER_ARM_LEN   = 290.0
CHEST_AXIS_X    = -165.0
CHEST_PLATE_Z0  = 115.0
STRUT_HOLES_Z   = (75.0, 115.0)
STRUT_INSERT_D, STRUT_INSERT_DEPTH = 5.6, 6.5
STRUT_BOLT_D    = 4.3
STRUT_Z0, STRUT_W, STRUT_T = 62.0, 32.0, 8.0
# ---------------- upper-arm roll ----------------
ROLL_RC     = 50.5
ROLL_HALF   = 32.0
ROLL_Z0     = 130.0
RAIL_STEM   = 3.0
RAIL_HEAD   = 6.0
RAIL_STEM_H, RAIL_HEAD_H = 10.0, 8.0
SLIDE_CLR   = 0.4
ROLL_SCREW_ANG = (-20.0, 0.0, 20.0)
ROLL_SCREW_D, ROLL_PILOT_D, ROLL_PILOT_DEPTH = 4.3, 3.4, 14.0
CARR_X0, CARR_ZTOP, CARR_Y = 41.0, 153.6, 16.0
BLOCK = (24.0, 26.0)
FOOT_PHI_X, FOOT_Z = 79.0, 75.0
FOOT_HOLES = 11.0
# ---------------- end stops ------
EXT_POST_Y     = -15.6
FLEX_BLOCK_Y   = 43.0
FLEX_BLOCK_Z   = (0.0, 80.0)
EXT2_TAB_Z     = -54.0
FLEX2_Y        = 44.0
FLEX2_Z        = (18.0, 46.0)
# ---------------- wiring ----------------
LEAD_NOTCH_W, LEAD_NOTCH_H = 12.0, 8.0
CLIP_D_IN, CLIP_WALL, CLIP_SLIT = 7.0, 2.0, 3.5
EAR_SLOT = 6.0
ZIP_W, ZIP_T = 4.2, 2.0
# ---------------- elbow relief (01_..._ELBOW_RELIEF) ----------------
RELIEF_MARGIN = 6.0                 # skin/padding margin around the modelled forearm
RELIEF_SWEEP  = (-5.0, 95.0)        # flexion range swept by the forearm cylinder (deg)

REPO = os.getcwd()
OUT = os.path.join(REPO, "cad", "freecad"); OUT_STEP = os.path.join(OUT, "step")
os.makedirs(OUT_STEP, exist_ok=True)


# =====================================================================================
# Small shape-tree layer: the part functions below build a tree of nodes; emit() turns
# the tree into FreeCAD features. rotate() follows the X-then-Y-then-Z convention.
# =====================================================================================
class N:
    def __init__(self, kind, label, **kw):
        self.kind, self.label, self.kw = kind, label, kw
        self.pl = App.Placement()
    def _t(self, pl):
        n = N(self.kind, self.label, **self.kw); n.pl = pl.multiply(self.pl); return n
    def translate(self, t): return self._t(App.Placement(V(*t), App.Rotation()))
    def rotate(self, r): return self._t(App.Placement(V(0, 0, 0), App.Rotation(r[2], r[1], r[0])))
    def __add__(self, o): return N("fuse", None, a=self, b=o)
    def __sub__(self, o): return N("cut", None, a=self, b=o)
    def __xor__(self, o): return N("common", None, a=self, b=o)

def box(x0, x1, y0, y1, z0, z1, label="Box"):
    return N("box", label, L=x1-x0, W=y1-y0, H=z1-z0).translate((x0, y0, z0))
def cube(x, y, z, c=(0, 0, 0), label="Box"):
    return N("box", label, L=x, W=y, H=z).translate((-x/2, -y/2, -z/2)).translate(c)
def cyl(h, r, center=True, label="Cylinder"):
    n = N("cyl", label, H=h, R=r)
    return n.translate((0, 0, -h/2)) if center else n
def cyl_z(h, r, c=(0, 0, 0), label="Cylinder"): return cyl(h, r, label=label).translate(c)
def cyl_x(h, r, c=(0, 0, 0), label="Cylinder"): return cyl(h, r, label=label).rotate([0, 90, 0]).translate(c)
def sphere(r, c=(0, 0, 0), label="Sphere"): return N("sphere", label, R=r).translate(c)
def rbox(x0, x1, y0, y1, z0, z1, r=3.0, label="RoundedBox"):
    """box with every edge rounded: inner box offset outward by r (arc join).
    Where a side is exactly 2r the core would be flat, so the radius is shrunk by a few microns."""
    r = min(r, (min(x1-x0, y1-y0, z1-z0)-0.01)/2)
    return N("offset", label, src=box(x0+r, x1-r, y0+r, y1-r, z0+r, z1-r, label=label+"Core"), r=r)
def rtaper(secA, secB, r=3.0, label="RoundedTaper"):
    """rounded hull of two box sections (x0,x1,y0,y1,z0,z1): convex hull of the inner corners, offset by r"""
    pts = []
    for (x0, x1, y0, y1, z0, z1) in (secA, secB):
        pts += [(x, y, z) for x in (x0+r, x1-r) for y in (y0+r, y1-r) for z in (z0+r, z1-r)]
    return N("offset", label, src=N("hull", label+"Hull", pts=pts), r=r)
def capsule_chain(wps, r, label="Arch"):
    """hull of spheres along a polyline = cylinders between waypoints + a sphere at each waypoint"""
    n = None
    for i, (p, q) in enumerate(zip(wps[:-1], wps[1:])):
        p, q = V(*p), V(*q); d = q-p
        c = N("cyl", f"{label}Segment{i+1}", H=d.Length, R=r)
        c.pl = App.Placement(p, App.Rotation(V(0, 0, 1), d))
        n = c if n is None else n+c
    for i, p in enumerate(wps): n = n+sphere(r, p, label=f"{label}Joint{i+1}")
    return n
def revolve_poly(pts, a0, a1, label="Revolution"):
    """revolve an (r,z) polygon about Z from angle a0 to a1 (deg, from +X toward +Y)"""
    c, s = math.cos(math.radians(a0)), math.sin(math.radians(a0))
    return N("revol", label, nodes=[(r*c, r*s, z) for r, z in pts], base=(0, 0, 0), axis=(0, 0, 1), angle=a1-a0)
def slot_x(y, z, d, length, x_c, depth, label="Slot"):
    return (cyl_x(depth, d/2, (x_c, y, z-length/2), label+"End") + cyl_x(depth, d/2, (x_c, y, z+length/2), label+"End")
            + cube(depth, d, length, (x_c, y, z), label+"Middle"))


def _hull_shape(pts):
    """convex hull of a few points as a planar-faced solid (pure Python, fine for 16 points)"""
    P = [V(*p) for p in pts]; n = len(P); planes = {}
    for i in range(n):
        for j in range(i+1, n):
            for k in range(j+1, n):
                nm = (P[j]-P[i]).cross(P[k]-P[i])
                if nm.Length < 1e-9: continue
                nm.normalize(); d = nm.dot(P[i])
                side = [nm.dot(q)-d for q in P]
                if all(s <= 1e-6 for s in side) or all(s >= -1e-6 for s in side):
                    if any(s > 1e-6 for s in side): nm, d = -nm, -d
                    key = (round(nm.x, 6), round(nm.y, 6), round(nm.z, 6), round(d, 4))
                    planes[key] = (nm, d)
    faces = []
    for nm, d in planes.values():
        on = [q for q in P if abs(nm.dot(q)-d) < 1e-6]
        uniq = []
        for q in on:
            if all((q-u).Length > 1e-9 for u in uniq): uniq.append(q)
        # 2D convex hull of the points on this plane (monotone chain), outward normal = nm
        u = uniq[1]-uniq[0]; u.normalize(); w = nm.cross(u)
        q2 = sorted(((q.dot(u), q.dot(w)), q) for q in uniq)
        def half(seq):
            h = []
            for p in seq:
                while len(h) >= 2 and ((h[-1][0][0]-h[-2][0][0])*(p[0][1]-h[-2][0][1])
                                       - (h[-1][0][1]-h[-2][0][1])*(p[0][0]-h[-2][0][0])) <= 1e-9:
                    h.pop()
                h.append(p)
            return h
        lo, hi = half(q2), half(q2[::-1])
        ring = [p[1] for p in lo[:-1]+hi[:-1]]
        faces.append(Part.Face(Part.makePolygon(ring+[ring[0]])))
    shell = Part.Shell(faces); shell.sewShape()
    solid = Part.Solid(shell)
    if solid.Volume < 0: solid.reverse()
    return solid


class Emitter:
    def __init__(self, doc): self.doc = doc; self.count = {}
    def name(self, label):
        k = self.count.get(label, 0)+1; self.count[label] = k
        return label if k == 1 else f"{label}{k:03d}"
    def flat(self, n, kind):
        if n.kind == kind and n.pl.isIdentity(): return self.flat(n.kw["a"], kind)+self.flat(n.kw["b"], kind)
        return [n]
    def emit(self, n, pl=None, label=None):
        pl = (pl or App.Placement()).multiply(n.pl); d = self.doc
        if n.kind == "box":
            o = d.addObject("Part::Box", self.name(n.label)); o.Length, o.Width, o.Height = n.kw["L"], n.kw["W"], n.kw["H"]; o.Placement = pl
        elif n.kind == "cyl":
            o = d.addObject("Part::Cylinder", self.name(n.label)); o.Height, o.Radius = n.kw["H"], n.kw["R"]; o.Placement = pl
        elif n.kind == "sphere":
            o = d.addObject("Part::Sphere", self.name(n.label)); o.Radius = n.kw["R"]; o.Placement = pl
            if "A3" in n.kw: o.Angle3 = n.kw["A3"]
        elif n.kind == "hull":
            o = d.addObject("Part::Feature", self.name(n.label)); s = _hull_shape(n.kw["pts"]); s.Placement = pl; o.Shape = s
        elif n.kind == "offset":
            src = self.emit(n.kw["src"], pl)
            o = d.addObject("Part::Offset", self.name(n.label)); o.Source = src; o.Value = n.kw["r"]
            o.Mode = "Skin"; o.Join = "Arc"; o.Fill = False; src.Visibility = False
        elif n.kind == "revol":
            p = d.addObject("Part::Polygon", self.name(n.label+"Profile"))
            p.Nodes = [pl.multVec(V(*q)) for q in n.kw["nodes"]]; p.Close = True; p.Visibility = False
            o = d.addObject("Part::Revolution", self.name(n.label)); o.Source = p
            o.Base = pl.multVec(V(*n.kw["base"])); o.Axis = pl.Rotation.multVec(V(*n.kw["axis"]))
            o.Angle = n.kw["angle"]; o.Solid = True
        elif n.kind == "fuse":
            kids = [self.emit(k, pl) for k in self.flat(n.kw["a"], "fuse")+self.flat(n.kw["b"], "fuse")]
            o = d.addObject("Part::MultiFuse", self.name(label or "Union")); o.Shapes = kids; o.Refine = True
            for k in kids: k.Visibility = False
        elif n.kind == "common":
            kids = [self.emit(k, pl) for k in self.flat(n.kw["a"], "common")+self.flat(n.kw["b"], "common")]
            o = d.addObject("Part::MultiCommon", self.name(label or "Intersection")); o.Shapes = kids
            for k in kids: k.Visibility = False
        elif n.kind == "cut":
            base = self.emit(n.kw["a"], pl)
            tools = [self.emit(k, pl) for k in self.flat(n.kw["b"], "fuse")]
            if len(tools) > 1:
                t = d.addObject("Part::MultiFuse", self.name("CutTools")); t.Shapes = tools
                for k in tools: k.Visibility = False
            else: t = tools[0]
            o = d.addObject("Part::Cut", self.name(label or "Cut")); o.Base = base; o.Tool = t; o.Refine = True
            base.Visibility = False; t.Visibility = False
        else: raise ValueError(n.kind)
        return o


# =====================================================================================
# Parts (ported from generator/make_aegis_v15.py)
# =====================================================================================
def cable_clip(x_face, y_c, z_c, length=10.0, open_dir=1):
    ro = CLIP_D_IN/2+CLIP_WALL; xc = x_face+ro-0.5
    c = cyl_z(length, ro, (xc, y_c, z_c), "CableClip") - cyl_z(length+2, CLIP_D_IN/2, (xc, y_c, z_c), "CableClipBore")
    c -= box(xc-0.5*CLIP_SLIT, xc+0.5*CLIP_SLIT, min(y_c, y_c+open_dir*(ro+1)), max(y_c, y_c+open_dir*(ro+1)),
             z_c-length/2-1, z_c+length/2+1, "CableClipSlit")
    base = box(x_face-1.0, x_face+1.5, y_c-ro, y_c+ro, z_c-length/2, z_c+length/2, "CableClipBase")
    return c+base

def zip_slot_x(y, z, x0, x1):
    return box(x0, x1, y-ZIP_T/2, y+ZIP_T/2, z-ZIP_W/2, z+ZIP_W/2, "ZipTieSlot")

def cuff(circ, length, zc, z_top, z_bot):
    r_in = circ/(2*math.pi)+CLEAR; r_out = r_in+WALL; px = r_out+PLATE_T
    body = cyl_z(length, r_out, (0, 0, zc), "SaddleShell")
    body += box(r_out-14, px, -PLATE_W/2, PLATE_W/2, z_bot, z_top, "SaddlePlate")
    body -= cyl_z(abs(z_top-z_bot)+length+200, r_in, (0, 0, zc), "ArmBore")
    xcut = r_out*math.cos(math.radians(ARC_HALF))
    body -= box(-(r_out+6), xcut, -(r_out+6), (r_out+6), zc-length/2-1, zc+length/2+1, "SaddleTrim")
    r_mid = r_in+WALL/2
    for dz in (-length*.26, length*.26):
        for s in (-1, 1):
            a = s*(ARC_HALF-14)
            body -= cube(WALL*3, 3.5, STRAP_W, label="StrapSlot").rotate([0, 0, a]).translate(
                [r_mid*math.cos(math.radians(a)), r_mid*math.sin(math.radians(a)), zc+dz])
    return body, r_in, r_out, px

def roll_rail():
    rc = ROLL_RC; z0 = ROLL_Z0; z1 = z0+RAIL_STEM_H; z2 = z1+RAIL_HEAD_H
    pts = [(rc-RAIL_STEM, z0), (rc+RAIL_STEM, z0), (rc+RAIL_STEM, z1), (rc+RAIL_HEAD, z1), (rc+RAIL_HEAD, z2),
           (rc-RAIL_HEAD, z2), (rc-RAIL_HEAD, z1), (rc-RAIL_STEM, z1)]
    r = revolve_poly(pts, -ROLL_HALF, ROLL_HALF, "RollRail")
    for a in ROLL_SCREW_ANG:
        x = rc*math.cos(math.radians(a)); y = rc*math.sin(math.radians(a))
        r -= cyl_z(RAIL_STEM_H+RAIL_HEAD_H+2, ROLL_SCREW_D/2, (x, y, (z0+z2)/2), "ScrewHole")
        r -= cyl_z(4.0, 4.2, (x, y, z2-1.0), "Counterbore")
    return r

def roll_slot():
    rc = ROLL_RC; z0 = ROLL_Z0; z1 = z0+RAIL_STEM_H; z2 = z1+RAIL_HEAD_H; c = SLIDE_CLR
    pts = [(rc-RAIL_STEM-c, z0-3), (rc+RAIL_STEM+c, z0-3), (rc+RAIL_STEM+c, z1-c), (rc+RAIL_HEAD+c, z1-c),
           (rc+RAIL_HEAD+c, z2+c), (rc-RAIL_HEAD-c, z2+c), (rc-RAIL_HEAD-c, z1-c), (rc-RAIL_STEM-c, z1-c)]
    return revolve_poly(pts, -55.0, 55.0, "RollTSlot")

def upper_cuff(primary=True, backup=True):
    zc = GAP_UP+UPPER_CUFF_LEN/2
    z_lo = -SV_SHAFT_END-SV_CLEAR-CRADLE_WALL-4
    body, r_in, r_out, px = cuff(UPPER_ARM_CIRC, UPPER_CUFF_LEN, zc, GAP_UP+UPPER_CUFF_LEN, z_lo)
    py = SV_W+2*SV_CLEAR
    z0 = -SV_SHAFT_END-SV_CLEAR; z1 = SV_L-SV_SHAFT_END+SV_CLEAR
    cradle = box(px, px+CRADLE_H, -(py/2+CRADLE_WALL), py/2+CRADLE_WALL, z0-CRADLE_WALL, z1+CRADLE_WALL, "Cradle")
    cradle -= box(px-0.01, px+CRADLE_H+1, -py/2, py/2, z0, z1, "ServoPocket")
    zm_ = (z0+z1)/2
    for sz in (-1, 1):
        zin = zm_+sz*(z1-z0)/2; zout = zm_+sz*(EAR_Z/2+6.0)
        cradle += rbox(px, px+CRADLE_H, -(EAR_Y+9.0), EAR_Y+9.0, min(zin, zout), max(zin, zout), 2.0, "EarBoss")
    cradle -= box(px-0.01, px+CRADLE_H+1, -py/2, py/2, z0, z1, "ServoPocket")
    for sy in (-1, 1):
        for sz in (-1, 1):
            xc_ = px+CRADLE_H-EAR_PILOT_DEPTH/2+0.01
            for dz in (-EAR_SLOT/2+EAR_PILOT_D/2, EAR_SLOT/2-EAR_PILOT_D/2):
                cradle -= cyl_x(EAR_PILOT_DEPTH+0.01, EAR_PILOT_D/2, (xc_, sy*EAR_Y, zm_+sz*EAR_Z/2+dz), "EarPilot")
    cradle -= box(px-0.01, px+LEAD_NOTCH_H, -LEAD_NOTCH_W/2, LEAD_NOTCH_W/2, z1-0.5, z1+CRADLE_WALL+EAR_SLOT, "LeadNotch")
    body += cradle
    zm = (z0+z1)/2
    for sy in (-1, 1):
        for sz in (-1, 1):
            body -= slot_x(sy*EAR_Y, zm+sz*EAR_Z/2, 3.4, 10, px-3, 20, "EarBoltSlot")
    body -= cyl_x(PLATE_T+30, 9.0, (px-3, 0, 0), "ShaftClearance")
    x0 = px+0.0; x1 = px+48.0
    zc_bot = z0-CRADLE_WALL
    if primary:
        body += rtaper((x0, x1, EXT_POST_Y-20.0, EXT_POST_Y, -48.0, zc_bot+3), (x0+8, x1-12, EXT_POST_Y-12.0, EXT_POST_Y, -76.0, -70.0), 3.0, "ExtensionStop")
        yb = py/2+CRADLE_WALL-3.0
        body += rtaper((x0, x1, yb, yb+4.0, FLEX_BLOCK_Z[0], FLEX_BLOCK_Z[1]), (x0, x1-4.0, FLEX_BLOCK_Y-14.0, FLEX_BLOCK_Y, FLEX_BLOCK_Z[0]+12.0, FLEX_BLOCK_Z[1]-12.0), 4.0, "FlexionStop")
    xs0 = r_out-14.0
    if backup:
        body += rbox(xs0, px, -PLATE_W/2, -PLATE_W/2+9.0, EXT2_TAB_Z, z_lo+3.0, 2.5, "BackupExtensionStop")
        body += rbox(xs0, px, PLATE_W/2-3.0, FLEX2_Y, FLEX2_Z[0], FLEX2_Z[1], 2.5, "BackupFlexionStop")
    for a in ROLL_SCREW_ANG:
        body -= cyl_z(ROLL_PILOT_DEPTH+0.02, ROLL_PILOT_D/2, (ROLL_RC*math.cos(math.radians(a)), ROLL_RC*math.sin(math.radians(a)), ROLL_Z0-ROLL_PILOT_DEPTH/2+0.01), "RailPilot")
    for zc_ in (95.0, 118.0): body += cable_clip(px, PLATE_W/2-8.0, zc_, 10.0, 1)
    return body, px, r_out

def elbow_relief(body):
    """Cut the space the forearm sweeps through (forearm cylinder plus margin, swung about the elbow axis X
    through the flexion range) out of the upper cuff. The swept solid is built exactly: the cylinder at the
    two end angles, plus a spherical wedge about X between them, trimmed to the cylinder's width in X.
    (The wedge leaves out only a sliver near the forearm tip, 250 mm from the elbow, far from the cuff.)"""
    rf = FOREARM_CIRC/(2*math.pi)+RELIEF_MARGIN; L = 250.0
    a, b = RELIEF_SWEEP[0], RELIEF_SWEEP[1]
    tool = None
    for d in (a, b):
        c = cyl(L+0.0137, rf, center=False, label="ForearmAtLimit").translate((0, 0, -L)).rotate([d, 0, 0])
        tool = c if tool is None else tool+c
    rb = math.hypot(L, rf); t0 = math.radians(a)
    u0 = V(0, math.sin(t0), -math.cos(t0))           # forearm direction at the first limit
    m = App.Matrix(); ex, ez = u0, V(1, 0, 0); ey = ez.cross(ex)
    m.A11, m.A21, m.A31 = ex.x, ex.y, ex.z
    m.A12, m.A22, m.A32 = ey.x, ey.y, ey.z
    m.A13, m.A23, m.A33 = ez.x, ez.y, ez.z
    wedge = N("sphere", "ForearmSweepWedge", R=rb, A3=b-a); wedge.pl = App.Placement(m)
    tool = tool + (wedge ^ box(-rf, rf, -rb-1, rb+1, -rb-1, rb+1, "ForearmWidth"))
    return body - tool

def wrist_layers(px_f):
    horn = px_f+6+WS_H+4.0
    return dict(horn=horn, crank=(horn, horn+4), rod=(horn+4, horn+8), side=(horn+8, horn+12), ear_end=horn+3.0)

def torque_fins(px, link_x0):
    f = None
    for sy in (-1, 1):
        y0 = sy*FIN_Y-FIN_T/2; y1 = sy*FIN_Y+FIN_T/2
        fin = box(px-4, link_x0, min(y0, y1), max(y0, y1), BOLT_Z[1]-12, BOLT_Z[0]+12, "TorqueFin")
        for bz in BOLT_Z: fin -= cyl_x(14, 2.1, (link_x0-7, sy*FIN_Y, bz), "FinInsertPilot")
        f = fin if f is None else f+fin
    return f

def wrist_ear(body, px):
    xe = wrist_layers(px)["ear_end"]
    body += box(px-1, xe, -22.0, 22.0, WRIST_Z-16.0, WRIST_Z+16.0, "WristEar")
    body -= cyl_x(xe-px+6, (PIN_D+0.4)/2, ((px+xe)/2, 0.0, WRIST_Z), "PivotPinHole")
    body -= cyl_x(xe-px+6, (PIN_D+0.4)/2, ((px+xe)/2, BOLT_Y, WRIST_Z), "WristStopBoltHole")
    return body

def forearm_cuff(px_u):
    zc = -(GAP_DN+FOREARM_CUFF_LEN/2)
    z_top = -GAP_DN; z_bot = zc-FOREARM_CUFF_LEN/2-RAIL_LEN
    body, r_in, r_out, px = cuff(FOREARM_CIRC, FOREARM_CUFF_LEN, zc, z_top, min(z_bot, WRIST_Z-16.0))
    link_x0 = px_u+SV_H+HORN_STACK
    body += torque_fins(px, link_x0)
    for sy in (-1, 1):
        for rz in (z_bot+25, z_bot+70):
            body -= slot_x(sy*14, rz, 4.5, 8, px-3, 24, "WristRailSlot")
    return wrist_ear(body, px), px, r_out, link_x0

BAR_W, BAR_T   = 36.0, 8.0
BAR_STRAPS_Z   = (-85.0, -130.0)

def forearm_bar(px_u):
    r_in = FOREARM_CIRC/(2*math.pi)+CLEAR; r_out = r_in+WALL; px = r_out+PLATE_T
    link_x0 = px_u+SV_H+HORN_STACK
    z_top = -GAP_DN+10.0; z_bot_bar = WRIST_Z-16.0
    body = rbox(px-BAR_T, px, -BAR_W/2, BAR_W/2, z_bot_bar, z_top, 4.0, "ForearmBar")
    body += torque_fins(px, link_x0)
    for zc in BAR_STRAPS_Z:
        body -= box(px-BAR_T-1, px+1, -STRAP_W/2-0.5, STRAP_W/2+0.5, zc-1.9, zc+1.9, "StrapSlot")
    z_bot = -(GAP_DN+FOREARM_CUFF_LEN)-RAIL_LEN
    for sy in (-1, 1):
        for rz in (z_bot+25, z_bot+70):
            body -= slot_x(sy*14, rz, 4.5, 8, px-3, 24, "WristRailSlot")
    body = wrist_ear(body, px)
    for zz in (-60.0, -105.0, -160.0, -200.0):
        for sy in (-1, 1): body -= zip_slot_x(sy*5.2, zz, px-BAR_T-1, px+1)
    return body, px, r_out, link_x0

def link_plate(link_x0):
    L_top = 16.0; L_bot = BOLT_Z[1]-12
    p = box(link_x0, link_x0+LINK_T, -LINK_W/2, LINK_W/2, L_bot, L_top, "LinkPlate")
    p -= cyl_x(LINK_T+2, 4.0, (link_x0+LINK_T/2, 0, 0), "HornScrewHole")
    for a in (0, 90, 180, 270):
        p -= cyl_x(LINK_T+2, 1.7, (link_x0+LINK_T/2, 11*math.sin(math.radians(a)), 11*math.cos(math.radians(a))), "HornPatternHole")
    for sy in (-1, 1):
        for bz in BOLT_Z: p -= cyl_x(LINK_T+2, 2.2, (link_x0+LINK_T/2, sy*FIN_Y, bz), "FinBoltHole")
    return p

def servo_ph(px):
    z0 = -SV_SHAFT_END
    return box(px, px+SV_H, -SV_W/2, SV_W/2, z0, z0+SV_L, "ServoBody") + cyl_x(4, 10, (px+SV_H+2, 0, 0), "ServoHorn")

def wrist_mount(px_f):
    base = box(px_f, px_f+6, -PLATE_W/2, PLATE_W/2, -45, 45, "MountBase")
    for sy in (-1, 1):
        for rz in (-22.5, 22.5): base -= slot_x(sy*14, rz, 4.5, 8, px_f+3, 12, "RailSlot")
    py = WS_W+2*SV_CLEAR
    z0 = -WS_SHAFT_END-SV_CLEAR; z1 = WS_L-WS_SHAFT_END+SV_CLEAR
    wall = box(px_f+6, px_f+6+WS_H-12, -(py/2+4), py/2+4, z0-4, z1+4, "ServoWall")
    wall -= box(px_f+5.99, px_f+6+WS_H, -py/2, py/2, z0, z1, "ServoPocket")
    wall -= box(px_f+5.99, px_f+6+LEAD_NOTCH_H, -LEAD_NOTCH_W/2, LEAD_NOTCH_W/2, z1-0.5, z1+5.0, "LeadNotch")
    return base+wall

def wrist_servo_ph(px_f):
    z0 = -WS_SHAFT_END
    return box(px_f+6, px_f+6+WS_H, -WS_W/2, WS_W/2, z0, z0+WS_L, "WristServoBody") + cyl_x(6, 6, (px_f+6+WS_H+3, 0, 0), "WristServoHorn")

def hand_piece(px_f):
    L = wrist_layers(px_f); x0, x1 = L["side"]
    yp = HAND_T/2+DORSAL_FOAM
    zlo = -(0.52*HAND_LEN); zhi = -28.0
    plate = rtaper((-(HAND_W/2-6), (HAND_W/2-6), yp, yp+4, zhi-12.0, zhi), (-(HAND_W/2+2), (HAND_W/2+2), yp, yp+4, zlo, zlo+12.0), 1.9, "DorsalPlate")
    wing = rbox(HAND_W/2-8, x1, yp, yp+4, -56.0, zhi, 1.9, "Wing")
    side = box(x0, x1, -26.0, 34.0, -50.0, 22.0, "SidePlate")
    body = plate+wing+side
    body -= cyl_x(x1-x0+4, (PIN_D+0.4)/2, ((x0+x1)/2, 0.0, 0.0), "PivotHole")
    body -= cyl_x(x1-x0+4, 1.7, ((x0+x1)/2, LEVER_A, 0.0), "RodPinHole")
    # arc slot = the wrist stops: annular sector about X (radius ARC_R) from +LIM_EXT down to -LIM_FLEX, round ends
    w = (PIN_D+0.8)/2; xa, xb = x0-2, x1+2; a = math.radians(LIM_EXT)
    u = (-math.cos(a), math.sin(a))
    prof = [(x, (ARC_R+s*w)*u[0], (ARC_R+s*w)*u[1]) for x, s in ((xa, -1), (xb, -1), (xb, 1), (xa, 1))]
    body -= N("revol", "WristStopArcSlot", nodes=prof, base=(0, 0, 0), axis=(1, 0, 0), angle=LIM_EXT+LIM_FLEX)
    for k in (-LIM_FLEX, LIM_EXT):
        ak = math.radians(k)
        body -= cyl_x(x1-x0+4, w, ((x0+x1)/2, -ARC_R*math.cos(ak), ARC_R*math.sin(ak)), "ArcSlotEnd")
    for sx in (-1, 1):
        for z in (-48.0, -82.0): body -= cube(3.5, 8.0, 25.5, (sx*(HAND_W/2-16), yp+2, z), "StrapSlot")
    return body

def link_bar2(length, hole_ys, hd=3.4, w=12.0, t=4.0, extra=(), label="Link"):
    b = box(0, t, -w/2, length+w/2, -w/2, w/2, label)
    for y in hole_ys: b -= cyl_x(t+2, hd/2, (t/2, y, 0), "PinHole")
    for y, d in extra: b -= cyl_x(t+2, d/2, (t/2, y, 0), "HornHole")
    return b

def crank_part(): return link_bar2(RC, (RC,), extra=((0.0, 4.0), (8.0, 2.2), (-8.0, 2.2)), w=14.0, label="Crank")
def rod_part():   return link_bar2(ROD, (0.0, ROD), label="Rod")

def chest_plate():
    r_in = CHEST_CIRC/(2*math.pi)+CHEST_FOAM; r_out = r_in+CHEST_T; H = CHEST_H
    shell = cyl_z(H, r_out, (0, 0, H/2), "ChestOuter") - cyl_z(H+2, r_in, (0, 0, H/2), "ChestInner")
    shell = shell ^ box(-CHEST_W/2, CHEST_W/2, 0, r_out+10, 0, H, "FrontArcKeep")
    y_edge = math.sqrt(r_out**2-PAD_X**2)
    pad = box(-PAD_X, PAD_X, y_edge-3, r_out+4, PAD_Z[0], PAD_Z[1], "TrayPad")
    zc = (PAD_Z[0]+PAD_Z[1])/2
    for sx in (-1, 1):
        for sz in (-1, 1):
            pad -= cyl(10, 2.1, center=False, label="TrayInsertPilot").rotate([-90, 0, 0]).translate([sx*PATTERN[0]/2, r_out+4-10, zc+sz*PATTERN[1]/2])
    body = shell+pad
    r_mid = (r_in+r_out)/2
    def slot(phi, z, tang, vert, label):
        a = math.radians(phi); c = (r_mid*math.sin(a), r_mid*math.cos(a), z)
        return cube(14, tang, vert, label=label).rotate([0, 0, 90-phi]).translate(c)
    for ph in (-18, 18): body -= slot(ph, H-14, 25.5, 3.5, "ShoulderStrapSlot")
    half = math.degrees(math.asin((CHEST_W/2)/r_out))
    for sgn in (-1, 1):
        for z in (40, 110): body -= slot(sgn*(half-9), z, 3.5, 25.5, "TorsoStrapSlot")
    for xx in (79.0, 62.0):
        ph_ = math.degrees(math.asin(xx/r_mid))
        for dz in (-5.2, 5.2):
            body -= cube(14, ZIP_W, ZIP_T, label="ZipTieSlot").rotate([0, 0, 90-ph_]).translate([r_mid*math.sin(math.radians(ph_)), r_mid*math.cos(math.radians(ph_)), 46.0+dz])
    body -= chest_foot_holes_for_plate()
    return body, r_out

def tray_parts():
    L, W, Hh = TRAY_IN; o = TRAY_WALL
    tray = box(-L/2-o, L/2+o, -W/2-o, W/2+o, 0, TRAY_FLOOR+Hh, "Tray") - box(-L/2, L/2, -W/2, W/2, TRAY_FLOOR, TRAY_FLOOR+Hh+1, "TrayCavity")
    for sx in (-1, 1):
        for sy in (-1, 1):
            tray -= cyl(TRAY_FLOOR+2, 1.7, center=False, label="PadScrewHole").translate([sx*PATTERN[0]/2, sy*PATTERN[1]/2, -1])
            tray += cyl(Hh, 3.2, center=False, label="LidPost").translate([sx*(L/2-4), sy*(W/2-4), TRAY_FLOOR])
            tray -= cyl(Hh-2, 1.2, center=False, label="LidPostPilot").translate([sx*(L/2-4), sy*(W/2-4), TRAY_FLOOR+2])
    tray -= box(L/2-1, L/2+o+1, -10, 10, TRAY_FLOOR+6, TRAY_FLOOR+Hh-6, "CableExit")
    lid = box(-L/2-o, L/2+o, -W/2-o, W/2+o, 0, 3, "Lid")
    for sx in (-1, 1):
        for sy in (-1, 1): lid -= cyl(5, 1.7, center=False, label="LidScrewHole").translate([sx*(L/2-4), sy*(W/2-4), -1])
    lid -= cyl(5, ESTOP_D/2, center=False, label="EStopHole").translate([-L/2+22, 0, -1])
    return tray, lid

def _radial_cyl(h, r, phi_deg, t, z, r_c, label):
    a = math.radians(phi_deg)
    c = (r_c*math.sin(a)+t*math.cos(a), r_c*math.cos(a)-t*math.sin(a), z)
    return cyl(h, r, label=label).rotate([-90, 0, 0]).rotate([0, 0, -phi_deg]).translate(c)

def chest_foot_geometry():
    r_out = CHEST_CIRC/(2*math.pi)+CHEST_FOAM+CHEST_T
    return math.degrees(math.asin(FOOT_PHI_X/r_out)), r_out

def chest_foot_holes_for_plate():
    phi, r_out = chest_foot_geometry(); r_in = r_out-CHEST_T; cut = None
    for t in (-FOOT_HOLES, FOOT_HOLES):
        for dz in (-FOOT_HOLES, FOOT_HOLES):
            c = _radial_cyl(CHEST_T+8, STRUT_BOLT_D/2, phi, t, FOOT_Z+dz, (r_in+r_out)/2, "YokeFootBoltHole")
            cut = c if cut is None else cut+c
    return cut

def chest_link(px_u):
    strut_bx = px_u+STRUT_T+STRUT_T
    zs = UPPER_ARM_LEN
    st = rbox(px_u, px_u+STRUT_T, -STRUT_W/2, STRUT_W/2, CARR_ZTOP-6.0, zs+16.0, 4.0, "Strut")
    st = st + rbox(CARR_X0, px_u+STRUT_T, -CARR_Y, CARR_Y, ROLL_Z0+1.0, CARR_ZTOP, 3.0, "Carriage")
    st -= roll_slot()
    for zz in (190.0, 240.0):
        for sy in (-1, 1): st -= zip_slot_x(sy*5.2, zz, px_u-1, px_u+STRUT_T+1)
    st -= cyl_x(STRUT_T+2, 2.75, (px_u+STRUT_T/2, 0.0, zs), "ShoulderBoltHole")
    st -= cyl_x(3.0, 4.6, (px_u+1.0, 0.0, zs), "ShoulderBoltCounterbore")
    bx0 = strut_bx-STRUT_T
    bk = rbox(bx0, bx0+BLOCK[0], -BLOCK[1]/2, BLOCK[1]/2, zs-14.0, zs+36.0, 3.0, "GimbalBlock")
    bk -= cyl_x(18.0, 2.8, (bx0+9.0-0.01, 0.0, zs), "StrutInsertPilot")
    bk -= cyl(BLOCK[1]+4, 2.7, label="YokePinHole").rotate([90, 0, 0]).translate([bx0+BLOCK[0]/2, 0.0, zs+22.0])
    # arch yoke
    phi, r_out = chest_foot_geometry(); a = math.radians(phi); r = r_out+10.0
    foot = (CHEST_AXIS_X+r*math.sin(a), r*math.cos(a), CHEST_PLATE_Z0+FOOT_Z)
    bxs = strut_bx-STRUT_T+BLOCK[0]/2
    wp = [foot, (foot[0], foot[1], foot[2]+60), (CHEST_AXIS_X+105.0, 60.0, zs+45.0), (-30.0, 10.0, zs+70.0),
          (40.0, 0.0, zs+72.0), (bxs, 0.0, zs+62.0), (bxs, 0.0, zs+52.0)]
    arch = capsule_chain(wp, 8.0, "Arch")
    foot_l = cyl_z(CHEST_H+200, r_out+12, label="FootOuter") - cyl_z(CHEST_H+400, r_out, label="FootInner")
    foot_l = foot_l ^ box(FOOT_PHI_X-20, FOOT_PHI_X+20, 1, r_out+20, FOOT_Z-20, FOOT_Z+20, "FootKeep")
    for t in (-FOOT_HOLES, FOOT_HOLES):
        for dz in (-FOOT_HOLES, FOOT_HOLES):
            foot_l -= _radial_cyl(14.0, STRUT_INSERT_D/2, phi, t, FOOT_Z+dz, r_out+7.0, "FootInsertPilot")
    arch += foot_l.translate([CHEST_AXIS_X, 0, CHEST_PLATE_Z0])
    bxc = bx0+BLOCK[0]/2
    for sy in (-1, 1):
        yc = sy*(BLOCK[1]/2+0.6+3.0)
        arch += rbox(bxc-14.0, bxc+14.0, yc-3.0, yc+3.0, zs+6.0, zs+60.0, 3.0, "ClevisEar")
    arch -= cyl(60, 2.7, label="YokePinHole").rotate([90, 0, 0]).translate([bxc, 0.0, zs+22.0])
    return dict(strut=st, block=bk, yoke=arch)

def body_reference():
    r_t = CHEST_CIRC/(2*math.pi)
    torso = cyl_z(420, r_t, (CHEST_AXIS_X, 0, CHEST_PLATE_Z0+60), "Torso")
    arm = cyl_z(UPPER_ARM_LEN, UPPER_ARM_CIRC/(2*math.pi), (0, 0, UPPER_ARM_LEN/2), "UpperArm")
    fore = cyl_z(FOREARM_LEN, FOREARM_CIRC/(2*math.pi), (0, 0, -FOREARM_LEN/2), "Forearm")
    shoulder = sphere(52, (0, 0, UPPER_ARM_LEN), "Shoulder")
    return torso, arm+fore+shoulder


# =====================================================================================
def save(node, name, label):
    doc = App.newDocument(name.replace("-", "_"))
    o = Emitter(doc).emit(node, label=label)
    for x in doc.Objects:
        if x is not o and x.Label == label: x.Label = label+"Body"
    o.Label = label
    doc.recompute()
    bad = [x.Name for x in doc.Objects if hasattr(x, "isValid") and not x.isValid()]
    sh = o.Shape
    ok = sh.isValid() and not bad
    path = os.path.join(OUT, name+".FCStd")
    if os.path.exists(path): os.remove(path)
    doc.saveAs(path)
    sh.exportStep(os.path.join(OUT_STEP, name+".step"))
    line = f"{name:52s} features={len(doc.Objects):4d} solids={len(sh.Solids)} valid={ok} vol={sh.Volume:12.1f} {'' if ok else bad}"
    print(line); App.Console.PrintMessage(line+"\n")
    with open(os.path.join(OUT, "build_log.txt"), "a") as f: f.write(line+"\n")
    App.closeDocument(doc.Name)

if __name__ == "__main__" or True:
    S_Z = -(GAP_DN+FOREARM_CUFF_LEN/2)-FOREARM_CUFF_LEN/2-RAIL_LEN+47.5
    up, px_u, _ = upper_cuff()
    fa, px_f, _, lx0 = forearm_cuff(px_u)
    fb, _, _, lxb = forearm_bar(px_u)
    tray, lid = tray_parts()
    cl = chest_link(px_u)
    torso, limbs = body_reference()
    parts = [
        (up, "01_upper_cuff_with_servo_cradle", "UpperCuff"),
        (elbow_relief(up), "01_upper_cuff_with_servo_cradle_ELBOW_RELIEF", "UpperCuffElbowRelief"),
        (fa, "02_forearm_cuff_with_torque_fins_and_wrist_rail", "ForearmCuff"),
        (fb, "02B_forearm_straight_bar_with_torque_fins", "ForearmStraightBar"),
        (link_plate(lx0), "03_link_plate_DS51150", "LinkPlate"),
        (wrist_mount(px_f).translate([0, 0, S_Z]), "04_OPTIONAL_wrist_servo_mount", "WristServoMount"),
        (servo_ph(px_u), "05_DS51150_PLACEHOLDER_not_printable", "DS51150Placeholder"),
        (chest_plate()[0], "06_chest_plate_RIGHT_ARM", "ChestPlate"),
        (tray, "07_electronics_tray", "ElectronicsTray"),
        (lid, "08_tray_lid_with_estop_hole", "TrayLid"),
        (hand_piece(px_f), "09_OPTIONAL_hand_piece_dorsal_plate", "HandPiece"),
        (crank_part(), "10_OPTIONAL_wrist_crank", "WristCrank"),
        (rod_part(), "11_OPTIONAL_wrist_rod", "WristRod"),
        (wrist_servo_ph(px_f).translate([0, 0, S_Z]), "12_WRIST_SERVO_PLACEHOLDER_not_printable", "WristServoPlaceholder"),
        (cl["strut"], "14_shoulder_strut", "ShoulderStrut"),
        (cl["block"], "15_gimbal_block", "GimbalBlock"),
        (cl["yoke"], "16_chest_yoke_arch", "ChestYokeArch"),
        (torso, "17_BODY_REFERENCE_torso_not_printable", "TorsoReference"),
        (limbs, "18_BODY_REFERENCE_arm_not_printable", "ArmReference"),
        (roll_rail(), "20_roll_rail", "RollRail"),
    ]
    only = os.environ.get("AEGIS_ONLY")
    if os.path.exists(os.path.join(OUT, "build_log.txt")): os.remove(os.path.join(OUT, "build_log.txt"))
    for node, name, label in parts:
        if only and not name.startswith(only): continue
        save(node, name, label)
