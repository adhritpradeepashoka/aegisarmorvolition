Interactive physics simulation (browser, three.js). Work in progress.

## AI development disclosure

The browser-based physics simulator was written by AI, as I dont have the personal expertise to build it. It is a work in progress, and its physical parameters and simulation results should be treated as estimates rather than experimentally validated engineering results. I created it for the reviewer's ease.

The simulator includes a torso model and translucent arm and hand visuals to show the exoskeleton in relation to a human body. These provide anatomical and positional context for viewing the mechanism. They are visual elements of the scene and are not structural components of the exoskeleton.

Models the elbow servo (PD control, torque limit, printed stops), the optional hinged wrist (crank and rod linkage), the chest support (shoulder flexion, abduction, upper-arm roll on a curved rail) and the gravity load on each joint.

The STL files in `stl/` are test geometry in the assembly frame, not the submitted design. Servo specs other than the DS51150 stall figures, the wrist servo class, masses, centres of mass and stop stiffness are assumptions. See the notes in the side panel of the page.

Run locally: serve the repo root with any static server (for example `python3 -m http.server`) and open `sim/index.html`.
