> **Note:** `test-files/` is the old v12 set. Current parts are in `full-size-v15/` (generator in `generator/`).

# Aegis Armor (Black Carapace + Aegis)

Hack Club **Fallen** submission by Adhrit Pradeep (Hack Club: adhrit2012).

A wearable system for the right arm: an **EMG sleeve** ("Black Carapace": steel-thread electrodes on a tight shirt sleeve, read by Upside Down Labs Muscle BioAmp Candy boards) driving a **servo elbow exoskeleton** ("Aegis": DS51150 servo at the elbow, optional wrist joint, chest support). Related to the Volition / NPG Lite project.

> **Status: early. Nothing here is a finished or tested design yet.**
> TODO (Adhrit): replace this paragraph with your own description of what you are building and why.

## Repository layout

| Folder | What goes there |
|---|---|
| `cad/` | **Your own** Tinkercad / FreeCAD design files and exports (the files Fallen reviews). |
| `firmware/` | Code for the NPG Lite / servo controller (torque limit, current limit, kill switch). |
| `journal/` | Photos and notes that go with your Fallen journal entries. |
| `docs/` | Design notes, safety notes, measurements. |
| `sim/` | Interactive physics simulation of the elbow (open `sim/index.html` through a web server, or enable GitHub Pages and visit `/sim/`). |
| `test-files/` | Placeholder STLs used only for testing in CircuitBench. See note below. |
| `bom.csv` | Bill of materials (provisional, see `docs/bom-notes.md`). |

## Safety

This device puts motor torque on a human arm. Required before any real use: a hardware kill switch (e-stop), physical end stops on every joint, a software torque limit and a current limit. See `docs/safety.md`.
