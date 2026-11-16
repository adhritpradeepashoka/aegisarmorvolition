# Black Carapace garment: plan (NOT BUILT YET)

**Status: the garment has not been made.** Nothing below is measured on a real garment. It is a plan based on published sources and research done on 14 Nov 2026, and every number marked "check" must be measured on the finished garment.

## Goal
- 4 x Muscle BioAmp Candy (4 EMG channels) with every electronic part on the chest plate. Steel-thread electrodes sewn into a tight garment, with the thread running all the way to the chest plate instead of wires. The garment has no electronics, so it can be washed once the cables are unclipped from the chest studs.

## Base garment: test both a sleeve and a shirt
Neither has been bought or sewn yet. The plan is to build the same electrode layout on two bases and compare them:
- **Arm sleeve** (tight, stretchy): quick and cheap to prototype on. Good for trying electrode positions, pad size and strap pressure. It stops at the shoulder, so the threads need a separate path (or a short carrier piece) to reach the chest plate.
- **Full-sleeved shirt** (swim shirt or rash guard): the likely final base, because it carries the threads across the shoulder and over the chest to the plate and holds the pads against the skin.
- For both, choose a snug, very stretchy fabric and sew the steel thread onto a scrap first to check it. Nylon or polyester with elastane is a reasonable guess but untested. The textile-electrode study below recommends at least about 10 mmHg of clothing pressure over the electrodes.
- Test-fit electrode positions on the wearer before sewing anything.

## Routing: all electronics on the chest plate (chosen design)
Every electronic part sits on the chest plate. The garment has no boards, no battery and no wires, only thread, pads and studs. Each channel's IN+ and IN- thread is sewn straight into its embroidered pad (no stud at the pad) and runs along the arm, over the shoulder, to the chest. All 4 channels share one reference electrode. That is 8 signal runs plus 1 reference run, each as long as the pad-to-chest distance (**measure it on the wearer**).

**Detachable joint, at the chest only:** the runs end at small snap studs on the garment's chest. Each Candy's cable clips onto its studs there. To wash the garment, unclip the cables and wash. 8 signal studs, plus the reference thread branching to 4 studs (one for each cable's REF clip), so 12 studs in total. The stud size must match what the cable grabs (likely the 4 mm ECG type, to be confirmed by trying the cable on a gel electrode or the Band).

**Accepted risk:** these are long, high-impedance electrode leads, which pick up mains hum, motion artifact and coupling from the servo wiring. A 2025 Science Advances study (Lee et al., as found in the 14 Nov 2026 research) found unshielded long wiring gave an SNR of at most about 3 dB, against about 31 dB shielded. Look up the paper before relying on those numbers. This design takes the risk on purpose, and the noise is to be characterised on the bench (plan below). Mitigations, all **untested**:
- Run each channel's IN+/IN- pair tightly together or twisted, so both pick up the same noise and the Candy's differential input cancels it.
- Insulate every run, and add a conductive-fabric shield around the bundle, tied to REF/GND at the chest end.
- Keep the bundle away from the servo and buck-converter wiring.
- Keep the runs as short as possible, strain-relieved, and flat against the body so they cannot swing (motion artifact).

**Fallback:** if the long leads turn out unusable, move each Candy onto the garment next to its pads and run only 3V3, GND and 4 outputs to the chest. That would need a removable board mount on the garment (not designed).

## Stud mounting (salvaged studs, plan)
The chest studs come from the builder's own disposable ECG electrodes. The studs are solid metal and have no eyelet.
1. Cut each stud out with a ring of the foam around it. Peel off the adhesive backing and wipe the gel off the stud and the foam.
2. Wrap the conductive thread several times tightly around the stud's neck, under the head. This is the electrical joint. Tie off.
3. Sew the foam ring to the garment with ordinary thread, with stitches all around it. A small piece of felt under the foam spreads the pull. This is the mechanical hold.
4. Test every stud with a multimeter from the end of the thread to the top of the stud (should read close to 0 ohm), then tug firmly and check the reading does not jump.
5. Try this on a scrap of fabric first. If it holds, repeat it on the garment.

**Simpler fallback for the first prototype:** skip the studs, sew each thread end through a small ring or eyelet, solder or crimp a thin flexible wire to the ring, and strain-relieve the wire to the fabric a few centimetres away. This gives up washing the garment with the cables clipped on.

Thread cannot be soldered directly (stainless thread has an oxide layer that ordinary solder does not wet, and the heat damages the fibres).

## Shared reference
- All 4 channels share **one reference electrode** on a bony, electrically quiet spot, away from the muscles being read (exact spot to decide on the wearer).
- Plausible but **not documented by Upside Down Labs for the Candy**. Their 2-channel EXG Pill guide ties both references to one electrode, and their NPG Lite multichannel kit uses one REF cable. Validate with 2 boards first: compare noise and crosstalk with a shared and a separate reference.

## Noise characterisation plan (to do on the bench)
Record the same muscle with the XIAO ADC at a fixed sample rate (for example 1 kHz), the same Candy and the same cable, and compare:
1. **Baseline:** gel electrodes with the 50 cm official cable, arm still and arm moving.
2. Sewn pads, thread run to the chest at the real length, no shield.
3. Same, with the shield and with the pair twisted.
4. Same, with the servo powered and moving, and the buck converter running.
5. Shared reference against separate reference.
6. Sewn pad with a little electrode gel against dry.

For each: resting RMS noise (ADC counts), signal during a hard contraction, the resulting SNR, and the spectrum (look at 50 Hz mains and its harmonics, which land inside the Candy's 72 to 720 Hz band at 100, 150 Hz and so on, plus the servo's 50 to 330 Hz PWM and its harmonics). Repeat after sweating and after washing.

## Thread
- Stainless steel 316L, 2-ply, about 0.2 mm. Vendor resistance figures differ a lot (about 14 to 52 ohm per metre across listings), so **measure your own spool**. Thread resistance is negligible next to the Candy's input impedance (about 10^11 ohm).
- Stiff, like waxed thread. Rated for small currents (about 50 to 100 mA).
- Quantity: 9 runs of 0.5 to 1 m before electrode stitching, which often uses several more metres. Plan about one 23 m reel per garment.

## Electrodes
- Embroidered pads: skin-electrode impedance falls as the embroidered area grows, so make pads large and dense. A 2020 textile-electrode EMG study (Polymers 12(10):2406, as found in the 14 Nov 2026 research) found that electrodes of 20 mm diameter or more at 10 mmHg or more matched gel Ag/AgCl, and that 15 to 20 mmHg is cited for reducing motion artifact. Above about 20 mmHg was uncomfortable in another study.
- The same study covered exposed conductive parts with TPU film so nothing unintended touched the skin.
- Dry textile electrodes usually have higher skin impedance than gel. Plan skin prep, and test with and without a little electrode gel.
- Textile electrodes are noisier in motion: a textile ECG garment study (Heart and Vessels 2019) found noise in 41% of textile recordings against 6% with conventional electrodes during trunk twisting.

## Insulation and crossing
- Bare steel thread shorts if traces touch or cross. Cover traces with a non-conductive stitch layer plus fusible TPU film or fabric paint, and keep the runs apart. Plan insulated crossings or avoid them. Only the electrode pads should touch skin.

## Washing and sweat
- Stainless steel is corrosion resistant. Coated threads wear faster than steel in published tests. Unclip the cables at the chest studs, hand wash gently, and test your own garment. Measure the thread resistance after sweat and washing.

## Across the shoulder
- The thread crosses the moving shoulder. Stitch with slack (zigzag or serpentine) and strain-relief both ends. Stitched thread changes resistance when stretched, and on raw electrode leads that can add motion noise. This part is untested design reasoning.

## To measure on the real garment
0. Actual thread length from each pad to the chest studs.
1. Resistance of each full thread run.
2. Noise: follow the noise characterisation plan above.
3. Resistance and signal after wearing, sweating, washing, and repeated cable clip/unclip at the chest studs.
5. Whether the 4 channels stay separate (no shorts between runs).
6. Shared against separate reference electrode.
7. Sleeve against shirt: signal quality, noise while moving, pad contact over time, comfort, and how the threads hold across the shoulder.

## Sources
- Research, 14 Nov 2026: the Lee et al. 2025, Polymers 2020 and Heart and Vessels 2019 findings above are reported from it, and I do not have direct links, so look the papers up before citing them.
- Embroidered textile EMG electrodes: https://www.ncbi.nlm.nih.gov/pmc/articles/PMC9268917/
- Contact pressure study (Sensors 2023): https://doaj.org/article/8aeccd5c47094fc19cd6f0bda2cf731d
- Embroidered traces, insulation, washing: https://www.mdpi.com/2673-4591/52/1/8
- Conductive thread washing and tension: https://www.ncbi.nlm.nih.gov/pmc/articles/PMC9656624/
- Thread specs: https://www.adafruit.com/products/640 and https://www.fabtolab.com/components/material-science/conductive-thread-2-ply-adafruit
- Candy specs: https://docs.upsidedownlabs.tech/hardware/bioamp/muscle-bioamp-candy/index.html
- Upside Down Labs multichannel kit (one REF cable): https://docs.upsidedownlabs.tech/kits/npg-lite-kits/npg-lite-beast/index.html
- EMG noise and cable guidance: https://pmc.ncbi.nlm.nih.gov/articles/PMC7594523/table/T3
