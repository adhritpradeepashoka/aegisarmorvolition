# BOM notes

`bom.csv` is **provisional**. Fallen's required BOM format was not published when this was written, so the columns are a guess (now compact: item, qty, inr_each, store, status); reshape it when the format is known.

Rules to keep in mind (from the Fallen rules as understood): parts you should design yourself (brackets, mounts, frames) should be designed, not bought as modules/kits. Check with Hack Club whether the Muscle BioAmp Candy boards count as acceptable components for this project.

Prices marked "est." in the status column are estimates, not looked up. Parts the builder already owns are 0. On 16 Nov the electronics were moved to Robu and Robocraze where they were in stock; the servo, Candy boards and steel thread stay with their special suppliers.

Design decisions reflected in the BOM:
- **No wrist servo.** It adds weight and little benefit, so it was dropped. The wrist parts (`04`, `09` to `13B`) in `full-size-v15/` and the wrist module in the simulator are left over from earlier versions and are not part of the current build.
- **Controller:** XIAO ESP32-S3, not an NPG Lite.
- **4 Muscle BioAmp Candy boards**, all on the chest plate.
- Power parts are a proposal; see `power.md`. Prices were seen on 14 Nov 2026 and change; blank cells were not checked.
- All 4 Candy boards sit on the chest plate with the rest of the electronics; the electrode threads run through the garment, and the cables clip onto studs at the chest so the garment can be washed. See `garment.md`.

## Per-row notes moved out of bom.csv (16 Nov 2026)

Old per-row notes and sources, kept word for word. The current prices and stock are in `bom.csv`.

## DS51150 servo (elbow), 12 V, 180 deg
- Old source: Probots PRO3841 (in stock, GST incl, 1-3 day shipping); cheaper: eTechRobot 2799, RoboticsDNA 2839, Rees52 1899 (stock unclear), AliExpress/aifitlab import about USD 43 (backordered)
- Notes: Request the Probots price (6999 incl. GST, seen 16 Nov 2026) so the grant covers the in-stock listing; buy cheaper only if the variant checks out. Need the plain DS51150: single shaft, 180 deg, horn included (not RDS dual-shaft with brackets, not SSG 270 deg). Datasheet: 9-12.6 V, stall 7.4/8.0/8.3 A at 10/12/12.6 V, 65x30x48 mm, 162-175 g, 300 mm lead. Prices seen 1899-14351 and some listings give wrong specs or may be clones: buy from a seller with returns and measure stall current on arrival. Listed size 65x30x48 mm differs from the 57x31x57 mm cradle in full-size-v15: measure the real servo before printing final parts. Ear/horn hole pattern and lead side unconfirmed

## Seeed XIAO ESP32-S3
- Old source: Already owned (new price about 790, Robocraze)
- Notes: Already owned, so no cost in the grant request. 3.3 V logic: whether the DS51150 accepts it is unconfirmed, bench-test at 12.6 V

## Muscle BioAmp Candy board
- Old source: Upside Down Labs store
- Notes: 4 in stock (backorder OK) on 14 Nov 2026. Each kit includes a 50 cm cable, a band and 3 gel electrodes while stock lasts. Boards sit on the chest plate. Check the Fallen module rule

## BioAmp Cable v3, 50 cm (spare)
- Old source: Upside Down Labs store
- Notes: Optional spares; 100 cm is 349

## Gel electrodes (100) and electrode gel
- Old source: Upside Down Labs store
- Notes: Gel electrodes 549 for 100, gel 199 (separate item). For validating the textile electrodes and as the reference

## Steel conductive thread, 316L 2-ply 23 m
- Old source: ThingBits (incl. GST)
- Notes: One reel per garment (sleeve and shirt); in stock 14 Nov 2026

## Fusible TPU film / fabric paint + non-conductive thread (trace insulation)
- Old source: (none)
- Notes: Price not checked

## Snap studs for the cable clips (solid metal 4 mm ECG studs)
- Old source: Salvaged from the builder's own disposable ECG electrodes (solid metal, no eyelet)
- Notes: 12 needed: 8 signal + 4 reference, at the garment's chest. Cut each stud out with a ring of foam, wipe off the gel, wrap conductive thread around the stud neck and sew the foam ring down; see docs/garment.md. Check the Candy cable clips onto them. Buy loose studs later if these wear out

## Conductive fabric (cable bundle shield)
- Old source: (none)
- Notes: Part of the chosen design (shield tied to REF/GND at the chest); price not checked

## Tight full-sleeved swim shirt / rash guard
- Old source: (none)
- Notes: Price not checked. One of the two garment test bases

## Tight stretchy arm sleeve
- Old source: (none)
- Notes: Price not checked. The other garment test base

## 3S LiPo pack 11.1 V 2200 mAh 35C, XT60 + JST-XH balance lead (Bonka or similar)
- Old source: Robu (Bonka 2200 mAh 35C, in stock 16 Nov, price to confirm); Robocraze 1599 (sold out 16 Nov); Quartz 1335 ex-GST; Probots 60C 1399 (out of stock)
- Notes: Chosen over 18650 cells (no welding or holder needed). About 24 Wh. A drone LiPo has no protection board: use a balance charger, the fuse and the firmware low-voltage cutoff (docs/power.md). Check the plug is XT60 and the balance lead is 4-wire. Keep it in a rigid case, never charge unattended, retire it if it puffs. Full charge is 12.6 V = the servo's max

## 3S LiPo balance charger (IMAX B3 Pro, AC, 2S/3S)
- Old source: Probots PRO600 (in stock, GST incl, pickup at Bangalore HQ); upgrade: IMAX B6 80W about 2500-2950 (needs a 12 V DC supply; many listings are copies)
- Notes: Plug-and-play balance charger, 800 mA. Charge on a non-flammable surface and stay nearby. Check the pack stops at 12.6 V on the first charge with a multimeter. Never use a phone charger

## LiPo safe charging bag + rigid case or pouch for the pack on the chest plate
- Old source: (none)
- Notes: Price not checked. Protects the pouch from crushing and fire while charging and worn

## Buck converter 12 V to 5 V, 3 A + Schottky diode to XIAO 5V pin
- Old source: Zbotic / Robu LM2596 or MP1584 module (about 60-100); Schottky diode a few rupees
- Notes: Price seen 16 Nov 2026 (LM2596S module 60 incl. GST on Zbotic, MP1584 91; LM2596 rated 2 A, 3 A max). The XIAO needs well under 1 A, so a small module is enough. The XIAO 5V pin takes external power only through a diode. Set the output to 5.0 V with a multimeter BEFORE connecting the XIAO. Keep it away from the thread runs (switching noise)

## INA226 current sensor module
- Old source: Sharvi Electronics, Bengaluru (ex-tax; REES52 199)
- Notes: Replace the module's shunt. The INA219 in the firmware saturates near 3.2 A, so firmware needs a port

## Shunt 5 mOhm, 1%, 1-2 W, Kelvin (4-wire)
- Old source: element14 India / Mouser India / DigiKey India
- Notes: Price not found. 5 mOhm gives 16.4 A full scale, 41.5 mV at 8.3 A, about 0.34 W at stall

## TVS diode (about 15 V) + bulk capacitor 470 uF+ low-ESR, servo bus
- Old source: (none)
- Notes: Price not checked. 12.6 V full charge equals the servo's max, and back-driving the elbow can push the bus above it; check the TVS clamp voltage against the servo rating, or charge to about 12.3 V instead

## 12 V 30 A relay (servo power contactor) + flyback diode + socket
- Old source: Robocraze T90 (others 69-270)
- Notes: Price seen 14 Nov 2026. Coil about 140 mA. Automotive relays can weld and have no contact feedback, so the firmware PWM-off path stays as a second layer

## 22 mm e-stop pushbutton, 2 NC contact blocks
- Old source: Amazon.in (2NC listings); Quartz Components basic e-stop 67
- Notes: Price for a 2NC unit not captured; the Quartz one does not state its contacts. Typical 22 mm e-stop DC-13 ratings are only 1.5-4 A at 24 V, so do not break servo current through it

## Blade fuse 10 A + inline holder
- Old source: (none)
- Notes: Price not checked. At the pack + line

## XT60 connectors (pair)
- Old source: (none)
- Notes: Price not checked

## Silicone wire 14-16 AWG
- Old source: (none)
- Notes: Price not checked. Servo power path

## Silicone wire 22-24 AWG
- Old source: (none)
- Notes: Price not checked. Signal and logic

## Logic level shifter or 5 V buffer (optional)
- Old source: (none)
- Notes: Only if the DS51150 is unreliable at a 3.3 V signal; price not checked

## Elbow angle sensor (potentiometer or magnetic encoder, optional)
- Old source: (none)
- Notes: The DS51150 has no position feedback; added for true joint angle. Price not checked

## Velcro strap 25 mm
- Old source: (none)
- Notes: For saddle plates / chest plate; price not checked

## M4 heat-set inserts
- Old source: (none)
- Notes: Strut mounts and servo ears; count when design is final

## M4 screws
- Old source: (none)
- Notes: Count when design is final

## M5 bolts and nyloc nuts
- Old source: (none)
- Notes: Shoulder pivot and other pivots; count when design is final

## Zip ties, small
- Old source: (none)
- Notes: Cable routing slots in the printed parts

## PETG filament
- Old source: (none)
- Notes: Already owned (so not in the grant request). PETG preferred over PLA near body heat; Bambu Lab A1 printing
