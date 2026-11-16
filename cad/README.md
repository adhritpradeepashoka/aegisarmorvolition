# Full-size Aegis parts, v15

## Folders (newest and most useful first)

| Folder | What it holds |
|---|---|
| `freecad/` | **Start here.** Editable FreeCAD source (`.FCStd`) for every part, plus STEP exports with real curved faces in `freecad/step/`. See `freecad/README.md`. |
| `old_steps/` | The earlier STEP files, converted from the STL meshes (triangle faces, not editable by dimension). Kept for reference. |
| `stl/` | Individual STL files for the parts, along with the `*_REFERENCE` assembly-preview meshes. |

The files marked `*_REFERENCE` are assembled-view previews. They position multiple components together in the assembly coordinate system, allowing the overall arrangement, relative positioning and orientation of the parts to be inspected. They are intended to make the assembly easier to understand and visualize alongside the individual part files.

**Still placeholder:** DS51150 ear-hole pattern, horn pattern and lead-exit side (not confirmed from a drawing). Measure the servo before printing.

`../test-files/` holds the older v12 print set and is outdated.

**Wrist parts:** the wrist servo has been dropped from the design (extra weight, little benefit). Files `04`, `09`, `10`, `11`, `12`, `13` and `13B` are leftovers and are not part of the current build.
