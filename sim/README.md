Interactive physics simulation (browser, three.js). Work in progress.

Models the elbow servo (PD control, torque limit, printed stops), the optional hinged wrist (crank and rod linkage), the chest support (shoulder flexion, abduction, upper-arm roll on a curved rail) and the gravity load on each joint.

The STL files in `stl/` are test geometry in the assembly frame, not the submitted design. Servo specs other than the DS51150 stall figures, the wrist servo class, masses, centres of mass and stop stiffness are assumptions. See the notes in the side panel of the page.

Run locally: serve the repo root with any static server (for example `python3 -m http.server`) and open `sim/index.html`.
