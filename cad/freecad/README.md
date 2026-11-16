# FreeCAD source files for the parts

One `.FCStd` file per part, matching the STL files in `../stl/` (same names, same coordinates: elbow axis = X through the origin, +X = outer side of the right arm, +Z = toward the shoulder, +Y = forward, millimetres). 

- **Editable:** each file is a tree of Part workbench features (Box, Cylinder, Sphere, Polygon + Revolution, Offset, Union, Cut, Intersection). Select any feature in the tree, change its size or placement in the Property view, and press Recompute. The final solid is the top object, named after the part (for example `LinkPlate`).
- **Rounded blocks** are a plain box (or a convex hull, for the tapered stops) with a `Part::Offset` on top; the offset `Value` is the corner radius.
- **Changing a measurement:** edit the feature that sets it (for example the box size or the cylinder radius) in the tree. Features that depend on it recompute.
- **`step/`** has a STEP file for every part, exported from these models. Unlike `../old_steps/` (converted from the STL meshes), these have real cylinders and planes, so they import cleanly into Onshape, Fusion or Tinkercad and can be measured and edited there.

Checked against the STL files in `../stl/`: every part matches to within 0.3% of its volume, except the chest plate (0.7%) and the chest yoke arch (1.5%). Those two differences come from the STL files approximating large curves with flat facets.

Placeholders stay placeholders here too: the DS51150 ear-hole pattern, horn pattern and lead-exit side are not confirmed. Measure the servo before printing.
