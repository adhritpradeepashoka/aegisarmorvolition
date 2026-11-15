# BOM notes

`bom.csv` is **provisional**. Fallen's required BOM format was not published when this was written, so the columns are a guess; reshape it when the format is known.

Rules to keep in mind (from the Fallen rules as understood): parts you should design yourself (brackets, mounts, frames) should be designed, not bought as modules/kits. Check with Hack Club whether the Muscle BioAmp Candy boards count as acceptable components for this project.

Blank price cells mean "not checked yet", not free.

Design decisions reflected in the BOM:
- **No wrist servo.** It adds weight and little benefit, so it was dropped. The wrist parts (`04`, `09` to `13B`) in `full-size-v15/` and the wrist module in the simulator are left over from earlier versions and are not part of the current build.
- **Controller:** XIAO ESP32-S3, not an NPG Lite.
- **4 Muscle BioAmp Candy boards**, all on the chest plate.
- Power parts are a proposal; see `power.md`. Prices were seen on 14 Nov 2026 and change; blank cells were not checked.
- All 4 Candy boards sit on the chest plate with the rest of the electronics; the electrode threads run through the garment, and the cables clip onto studs at the chest so the garment can be washed. See `garment.md`.
