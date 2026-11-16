"""Convert the reference STL files in cad/stl/ to faceted STEP files in cad/old_steps/.

Mesh-derived: faces are triangles (coplanar ones merged), so these are NOT
parametric models. Run from the repo root: python3 tools/stl_to_step.py
Skips the large *_REFERENCE assembly previews (their parts are converted one by one).
Needs: pip install cadquery-ocp
"""
import glob, os
from OCP.StlAPI import StlAPI_Reader
from OCP.TopoDS import TopoDS_Shape
from OCP.BRepBuilderAPI import BRepBuilderAPI_Sewing, BRepBuilderAPI_MakeSolid
from OCP.TopoDS import TopoDS, TopoDS_Compound
from OCP.BRep import BRep_Builder
from OCP.TopAbs import TopAbs_SHELL
from OCP.TopExp import TopExp_Explorer
from OCP.ShapeUpgrade import ShapeUpgrade_UnifySameDomain
from OCP.STEPControl import STEPControl_Writer, STEPControl_AsIs
from OCP.IFSelect import IFSelect_RetDone

SKIP = ("00_", "00B_", "13_", "13B_", "19_")  # big assembly previews; their parts are converted individually
for f in sorted(glob.glob("cad/stl/*.stl")):
    if os.path.basename(f).startswith(SKIP):
        continue
    out = "cad/old_steps/" + os.path.basename(f)[:-4] + ".step"
    shape = TopoDS_Shape()
    StlAPI_Reader().Read(shape, f)
    sew = BRepBuilderAPI_Sewing(1e-4)
    sew.Add(shape); sew.Perform()
    sewn = sew.SewedShape()
    comp = TopoDS_Compound()
    bb = BRep_Builder()
    bb.MakeCompound(comp)
    exp = TopExp_Explorer(sewn, TopAbs_SHELL)
    n = 0
    while exp.More():
        bb.Add(comp, BRepBuilderAPI_MakeSolid(TopoDS.Shell(exp.Current())).Shape())
        n += 1
        exp.Next()
    solid = comp if n else sewn
    u = ShapeUpgrade_UnifySameDomain(solid, True, True, True)
    u.Build()
    solid = u.Shape()
    w = STEPControl_Writer()
    w.Transfer(solid, STEPControl_AsIs)
    ok = w.Write(out) == IFSelect_RetDone
    print(("ok  " if ok else "FAIL"), out, round(os.path.getsize(out) / 1e6, 2), "MB")
