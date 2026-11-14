# Black Carapace garment: plan (NOT BUILT YET)

**Status: the garment has not been made.** Nothing below is measured on a real garment. It is a plan based on published sources, and every number marked "check" must be measured on the finished garment. The research links are at the bottom.

## Goal
- 4 x Muscle BioAmp Candy (4 EMG channels) on the chest plate, steel-thread electrodes sewn into a tight full-sleeved shirt, and the electrode threads run all the way to the chest plate, with no wires wherever possible.

## Base garment: test both a sleeve and a shirt
Neither has been bought or sewn yet. The plan is to build the same electrode layout on two bases and compare them:
- **Arm sleeve** (tight, stretchy): quick and cheap to prototype on. Good for trying electrode positions, pad size and strap pressure. It stops at the shoulder, so the threads would need a separate path (or a short carrier piece) to reach the chest plate.
- **Full-sleeved shirt** (swim shirt or rash guard): the likely final base, because it carries the threads across the shoulder and over the chest to the plate and holds the pads against the skin.
- For both, choose a snug, very stretchy fabric and sew the steel thread onto a scrap first to check it. Swim fabrics (nylon or polyester with elastane) are a reasonable guess but untested.
- Test-fit electrode positions on the wearer before sewing anything.

## Thread
- Stainless steel 316L, 2-ply, about 0.2 mm (e.g. Adafruit 640, sold in India by Fab.to.Lab). Vendor resistance figures differ a lot (about 14 to 52 ohm per metre across listings), so **measure your own spool**.
- Stiff, like waxed thread. Rated for small currents (about 50 to 100 mA), which is fine for 4 low-power boards. Check the Candy supply current and work out the voltage drop over your real run length.

## Routing: thread all the way to the chest plate (chosen design)
All 4 Candy boards sit on the chest plate. Nothing electronic is on the shirt sleeve. Each channel has two signal electrode threads (signal+ and signal-), sewn into the shirt and run along the arm, over the shoulder, to that channel's board. All 4 channels share **one reference electrode**, with one thread that goes to the REF input of every board. That is 8 signal threads plus 1 reference thread = 9 thread runs, each as long as the arm-to-chest distance (**measure it on the wearer**).

The thread's own resistance (tens of ohm) is tiny next to the Candy's input impedance (about 10^11 ohm), so resistance is not the problem. The risk is that these are long, high-impedance electrode leads, which pick up mains hum, motion artifact and coupling from the servo wiring. Published EMG guidance prefers short, twisted leads with the amplifier near the electrode. This design accepts that risk on purpose, so the layout has to reduce it. The measures below are design reasoning and are **untested**:

- Run each channel's pair side by side, as close together as the insulation allows (or twisted/braided), so both threads pick up the same noise and the Candy's differential input cancels most of it.
- Keep each channel's threads together as one bundle along the arm. Do not spread the electrodes of one channel apart.
- Keep thread runs away from the DS51150 and servo power wires and any motor leads.
- Shortest practical path, and put the chest plate boards as high and close to the shoulder as the plate allows.
- Strain-relieve and secure the threads so they do not swing against the body (motion artifact).
- Shared reference: tie the REF input of all 4 boards to the one reference thread. This is the intended design, but I have not verified it against the Candy documentation. Test it on the bench first (compare each channel's noise with a shared and with a separate reference), and ask Upside Down Labs if anything looks wrong.
- Put the single reference electrode on a bony, electrically quiet spot (e.g. near the elbow point or wrist bone, to be decided on the wearer), away from the muscles being read.

**Fallback:** if bench tests show the long leads are too noisy, move the boards onto the shirt sleeve next to the electrodes and run only VCC, GND and 4 x OUT to the chest plate. Build the garment so that change is possible.

## Electrodes
- Embroidered pads: skin-electrode impedance falls as the embroidered area grows, so make pads big and dense.
- Contact pressure matters. In one study the signal improved as the strap was tightened, and more than about 20 mmHg was uncomfortable. A tight shirt must press the pads evenly.
- Dry textile electrodes usually have higher skin impedance than gel Ag/AgCl. Plan skin prep, and test with and without a little electrode gel.

## Insulation and crossing
- Bare steel thread shorts if traces touch or cross. Cover traces with non-conductive thread or fabric paint, and keep the 6 runs apart. Plan insulated crossings or avoid them.

## Connections (the weak point)
- Soldered, crimped and snap connections are known failure points on garments. Published tests sew thread directly to board pads and measure resistance over 50 washes, so try a stitched pad connection with strain relief.
- The Candy has a JST PH connector. Decide how thread reaches it (sewn to a small pad board, or a crimp-to-thread adapter) and test it for pull strength.

## Washing and sweat
- Stainless steel is corrosion resistant. Coated threads wear faster than steel in published tests. Make the electronics removable and hand wash gently, but test your own garment.

## Across the shoulder
- The thread crosses the moving shoulder. Stitch with slack (zigzag or serpentine) and strain-relief both ends. Stitched thread changes resistance when stretched, and on raw electrode leads that can add motion noise. This part is untested design reasoning.

## To measure on the real garment
0. Actual thread length from each electrode to the chest plate.
1. Resistance of each full thread run.
2. Noise with the arm still, then moving, with the long leads (and against the on-sleeve fallback if it is too noisy).
3. Resistance and signal after wearing, sweating and washing.
4. Whether the 4 channels stay separate (no shorts between runs).
5. Sleeve vs shirt: signal quality, noise while moving, pad contact over time, comfort, and how well the threads hold across the shoulder.

## Sources
- Embroidered textile EMG electrodes: https://www.ncbi.nlm.nih.gov/pmc/articles/PMC9268917/
- Contact pressure study (Sensors 2023): https://doaj.org/article/8aeccd5c47094fc19cd6f0bda2cf731d
- Embroidered traces, insulation, washing: https://www.mdpi.com/2673-4591/52/1/8
- Conductive thread washing and tension: https://www.ncbi.nlm.nih.gov/pmc/articles/PMC9656624/
- Thread specs: https://www.adafruit.com/products/640 and https://www.fabtolab.com/components/material-science/conductive-thread-2-ply-adafruit
- Candy specs: https://robu.in/product/muscle-bioamp-candy
- EMG noise and cable guidance: https://pmc.ncbi.nlm.nih.gov/articles/PMC7594523/table/T3
