# FreeCAD source files for the reference parts

One `.FCStd` file per part, matching the STL files in `../` (same names, same coordinates: elbow axis = X through the origin, +X = outer side of the right arm, +Z = toward the shoulder, +Y = forward, millimetres). These are reference geometry, not my own CAD.

- **Editable:** each file is a tree of Part workbench features (Box, Cylinder, Sphere, Polygon + Revolution, Offset, Union, Cut, Intersection). Select any feature in the tree, change its size or placement in the Property view, and press Recompute. The final solid is the top object, named after the part (for example `LinkPlate`).
- **Rounded blocks** are a plain box (or a convex hull, for the tapered stops) with a `Part::Offset` on top; the offset `Value` is the corner radius.
- **Global measurements** (arm and chest circumference, servo size, strap width and so on) are numbers at the top of `generator/freecad/make_aegis_fcstd.py`. Change them there and rebuild every file:

  ```
  freecadcmd -c "exec(open('generator/freecad/make_aegis_fcstd.py').read())"
  ```
  Run from the repo root, with FreeCAD 1.0 or newer. `build_log.txt` lists every part with its volume and a validity check.
- **`step/`** has a STEP file for every part, exported from these models. Unlike `../step/` (converted from the STL meshes), these have real cylinders and planes, so they import cleanly into Onshape, Fusion or Tinkercad and can be measured and edited there.

Checked against the STL files in `../`: every part matches to within 0.3% of its volume, except the chest plate (0.7%), the arm reference (0.4%) and the chest yoke arch (1.5%). Those three differences come from the STL files approximating large curves with flat facets.

Placeholders stay placeholders here too: the DS51150 ear-hole pattern, horn pattern and lead-exit side are not confirmed. Measure the servo before printing.
