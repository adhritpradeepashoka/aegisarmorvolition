# Aegis Armor (Black Carapace + Aegis)

Hack Club **Fallen** submission by Adhrit Pradeep (Hack Club: adhrit2012).

## Bill of materials

Full file: [`bom.csv`](bom.csv). Prices in rupees, checked 16 Nov 2026; "est." means an estimate, not looked up. Notes and old sources are in [`docs/bom-notes.md`](docs/bom-notes.md).

<!-- BOM:START -->
| Item | Qty | Rs each | Store | Status |
|---|---:|---:|---|---|
| DS51150 servo, 12 V, 180 deg, single shaft | 1 | 6,999 | Probots | in stock 16 Nov |
| Seeed XIAO ESP32-S3 | 1 | 0 | owned | owned |
| Muscle BioAmp Candy board | 4 | 799 | Upside Down Labs | in stock 14 Nov; not at Robocraze |
| BioAmp cable v3 50 cm (optional spare) | 1 | 249 | Upside Down Labs | not rechecked |
| Gel electrodes x100 (optional) | 1 | 549 | Upside Down Labs | not rechecked |
| Electrode gel (optional) | 1 | 199 | Upside Down Labs | not rechecked |
| Steel thread 316L 2-ply 23 m | 2 | 1,060.82 | ThingBits | in stock 14 Nov |
| Fusible TPU film or fabric paint + plain thread | 1 | 300 | local/Amazon | est. |
| Snap studs, salvaged ECG studs x12 | 12 | 0 | owned | owned |
| Conductive fabric (shield) | 1 | 300 | local/Amazon | est. |
| Tight swim shirt / rash guard | 1 | 600 | local/Amazon | est. |
| Tight stretchy arm sleeve | 1 | 300 | local/Amazon | est. |
| 3S LiPo 11.1 V 2200 mAh 35C, XT60 | 1 | 1,600 | Robu | in stock 16 Nov; price est. (Robocraze 1971 sold out) |
| LiPo balance charger iMax B6AC 80W | 1 | 2,351 | Robocraze | in stock 16 Nov |
| LiPo charging bag + rigid pouch | 1 | 300 | local/Amazon | est. |
| Buck LM2596 12 V to 5 V, 3 A | 1 | 48 | Robocraze | in stock 16 Nov |
| Schottky diode 1N5819 (pack of 5) | 1 | 12 | Robocraze | SOLD OUT 16 Nov; find at Robu |
| INA260 current/voltage sensor, 15 A, I2C | 1 | 619 | Robocraze | in stock 16 Nov |
| TVS diode P6KE15A | 1 | 15 | Robu | est.; not at Robocraze |
| Capacitor 1000 uF 25 V | 1 | 9 | Robocraze | in stock 16 Nov |
| Relay 12 V 30 A T90 | 1 | 69 | Robocraze | listed 16 Nov; stock unconfirmed |
| Flyback diode 1N4007 (pack of 10) | 1 | 15 | Robocraze | in stock 16 Nov |
| E-stop 22 mm, 2 NC contacts | 1 | 67 | Quartz | not at Robocraze or Robu; contacts unconfirmed |
| Blade fuse 10 A + inline holder | 1 | 100 | Probots | est.; not at Robocraze |
| XT60 connector pair | 2 | 29 | Robocraze | in stock 16 Nov |
| Silicone wire 14-16 AWG, 2 m | 1 | 250 | Robu | est.; not at Robocraze |
| Silicone wire 22-24 AWG, 5 m | 1 | 120 | Robu | est.; not at Robocraze |
| Level shifter BSS138 4-ch (optional) | 1 | 31 | Robocraze | listed 16 Nov; stock unconfirmed |
| Elbow angle pot 10k (optional) | 1 | 40 | Robocraze | est. |
| Velcro 25 mm + zip ties | 1 | 150 | local/Amazon | est. |
| M4 inserts, M4 screws, M5 bolts + nyloc | 1 | 300 | local hardware | est. |
| PETG filament | 1 | 0 | owned | owned |
| **TOTAL (all rows)** | | **20,967.64** | | of which est. 4375 |
<!-- BOM:END -->

> **Note:** `test-files/` is the old v12 set. Current parts are in `cad/` (generator in `generator/`).

A wearable system for the right arm: an **EMG sleeve** ("Black Carapace": steel-thread electrodes on a tight full-sleeved shirt, read by Upside Down Labs Muscle BioAmp Candy boards) driving a **servo elbow exoskeleton** ("Aegis": DS51150 servo at the elbow, optional wrist joint, chest support). Related to the Volition / NPG Lite project.

> **Status: early. Nothing here is a finished or tested design yet.**

I've been passionate about brain-computer and body-computer interfaces for a long time, and I'm a (secretive) fan of Warhammer 40k, especially its tech. The Black Carapace, the interface space marines use to control their power armor, is the thing I've most wanted to build my own version of. It's a project I kept putting off, and Fallen gave me the push to start. This is my version: a tight full-sleeved shirt with steel-thread electrodes that reads my muscle signals (Black Carapace), driving a servo elbow exoskeleton for my right arm (Aegis).

## What it is and how to use it

- **Black Carapace** is a tight full-sleeved shirt with steel-thread electrodes. Muscle BioAmp Candy boards turn the muscle signal into a voltage the controller can read.
- **Aegis** is a one-arm servo exoskeleton: a DSSERVO DS51150 at the elbow (no wrist servo: it adds weight for little benefit), Velcro straps instead of rigid cuffs, mechanical end stops, and a chest support that links the arm to a chest plate.
- **To look at it:** open the interactive simulator (enable GitHub Pages, then visit `/sim/`). Drag the target angle, load the arm, change the supply voltage and torque limit, show or hide the wrist and the chest support, and press *Kill (e-stop)*.
- **Garment status:** the garment is not built yet. The plan (4 Candy boards on the chest plate, steel-thread electrode traces running through a tight shirt to the chest, tested on both a sleeve and a full shirt, with the noise to be characterised on the bench) is in `docs/garment.md`.
- **To read the parts:** `cad/` holds the 3D files, `docs/wiring.md` the wiring.

## Why I made it

I have a passion for brain-computer interfaces and I'm a fan of Warhammer 40k, to some extent. I always wanted a flexible interface suit that could assist me. I had the idea for a while, and when Fallen came up I decided to use the opportunity to at least design and implement it.

## Screenshots

### Full 3D assembly
Arm, chest support, an older wrist module (not part of the current build) and body reference in the simulator (placeholder geometry):

![Full 3D assembly in the simulator](docs/images/sim-full-assembly.png)

### PCB
No custom PCB in this build: the electronics are Upside Down Labs boards (Muscle BioAmp Candy x4) and a Seeed XIAO ESP32-S3 controller.

### Schematic / wiring diagram
Made in CircuitBench (concept diagram, stand-in parts, see `docs/wiring.md` for what each stand-in means):

![Wiring diagram](docs/images/wiring-circuitbench.png)

### 3D render (optional)
Parts only, then the elbow at 90 degrees:

![Parts only](docs/images/sim-parts-only.png)
![Elbow at 90 degrees](docs/images/sim-elbow-90deg.png)

### Anything else
- Live simulator: `/sim/` (GitHub Pages)
- Wiring project file for CircuitBench: `docs/circuitbench/aegis-wiring.circuitbench.json`
- Generator script for all parts: `generator/make_aegis_v15.py`

## For the build submission

- Hardware demo (SG90 desk version of the elbow, 5 s): [`docs/media/sg90-desk-demo.mp4`](docs/media/sg90-desk-demo.mp4)

  [![SG90 desk demo still](docs/images/sg90-desk-demo-still.png)](docs/media/sg90-desk-demo.mp4)

  What it shows: the printed elbow replica (0.4x mini test parts) being swung by an SG90 servo, driven from a small servo tester. What it is not: the full-size DS51150 arm, and nothing is worn or powered on a person. The EMG garment is not in this clip.

## Repository layout

| Folder | What goes there |
|---|---|
| `firmware/` | Code for the servo controller (torque limit, current limit, kill switch). |
| `journal/` | Photos and notes that go with your Fallen journal entries. |
| `docs/` | Design notes, safety notes, measurements. |
| `cad/`, `generator/` | Full-size part files and the script that makes them. |
| `sim/` | Interactive physics simulation of the elbow (open `sim/index.html` through a web server, or enable GitHub Pages and visit `/sim/`). |
| `test-files/` | Placeholder STLs used only for testing in CircuitBench. See note below. |
| `bom.csv` | Bill of materials (provisional, see `docs/bom-notes.md`). |

## Safety

This device puts motor torque on a human arm. Required before any real use: a hardware kill switch (e-stop), physical end stops on every joint, a software torque limit and a current limit. See `docs/safety.md`.
