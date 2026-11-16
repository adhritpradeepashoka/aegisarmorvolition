# Power (PROPOSED, not built, not tested)

This page was updated after research on 14 Nov 2026. Nothing here has been built or measured. Check every value against the real parts before wiring anything.

## DS51150 facts used (datasheet from the ANNIMOS/DSServo listing, as found in the 14 Nov 2026 research)
- Operating range **9 to 12.6 V** (an earlier version of these notes said 7.4 to 12.6 V, which mixed up the stall current with the voltage).
- Stall current 7.4 / 8.0 / 8.3 A at 10 / 12 / 12.6 V. Stall torque is 150 / 165 / 173 kg.cm in the datasheet, but other listings give 125 / 142 / 150 kg.cm. Plan around the lower figures.
- Control: 3-wire PWM, 500 to 2500 us pulses, 1500 us neutral, 50 to 330 Hz. **No position feedback.**
- Not published: duty-cycle rating, mounting-ear hole pattern, horn pattern, lead exit side, whether a 3.3 V signal is reliable. Measure the real servo.
- Several Indian listings give wrong specs. Do not size anything from listing text.

## Proposed architecture
- **Pack:** 3S LiPo drone pack, 11.1 V 2200 mAh 35C (about 24 Wh), with an XT60 plug and a JST-XH balance lead. Chosen on 16 Nov 2026 over a 3S 18650 pack to avoid cell holders and spot welding. 35C is far above the servo's stall current. Weight is probably about 140 to 190 g; weigh the real pack.
- **Protection (no BMS, drone LiPos have none):** charge only with a balance charger; 10 A fuse in the pack + line; a firmware low-voltage cutoff using the INA226 bus voltage (plan: about 3.3 V per cell, i.e. about 10 V, filtered so servo sag does not trip it; tune on the bench). Keep the pack in a rigid case on the chest plate, away from the arm joint; never charge it unattended; stop using it if it puffs or is dented. If you ever switch back to cylindrical cells, add a 3S BMS then.
- **Fuse:** 10 A blade fuse in the pack + line.
- **Voltage headroom problem:** a full 3S pack is 12.6 V, which is the servo's maximum, and back-driving the elbow can push the bus higher. Options: a TVS diode (about 15 V, check its clamp voltage) and a 470 uF+ low-ESR capacitor at the servo, or charge only to about 12.3 V with an adjustable charger. A 3S LiFePO4 pack would give headroom (about 10.8 V full, standard chemistry figures, not checked) at the cost of torque.
- **Servo power path:** pack + -> fuse -> relay contacts -> INA226 shunt -> DS51150 V+. The XIAO and the Candy boards are not powered from this path.
- **Logic power:** 12 V to 5 V buck -> Schottky diode -> XIAO 5V pin (the 5V pin accepts external power only through a diode). Candy boards and the INA226 run from the XIAO 3V3 pin, which can supply about 700 mA.
- **Common ground** between the battery, servo, buck converter and XIAO.

## E-stop
- Typical 22 mm e-stop contacts are rated only about 1.5 to 4 A at 24 V DC on inductive loads. A stalled DS51150 draws up to 8.3 A, so **do not break servo current through the e-stop.**
- Use a 12 V 30 A relay as the servo contactor, with the e-stop's NC contacts in series with the relay coil, a flyback diode across the coil, and the second NC block to a XIAO input so the firmware sees the state. The coil draws about 140 mA.
- An automotive relay is not a safety-rated contactor: its contacts can weld and it has no contact-state feedback. Keep the firmware PWM-off path and timeout as an independent second layer, and check the contacts after stall breaks.
- Add hard mechanical stops inside the elbow's range. At this torque a software angle limit is not enough.

## Current sensing
- The stock INA219 module (0.1 ohm shunt) saturates near 3.2 A and would dissipate about 6.4 W at 8 A. Any limit set above about 3.2 A does not work with it.
- Use an INA226 (36 V bus, 81.92 mV shunt range) with a 5 mOhm, 1%, 1 to 2 W Kelvin shunt: 16.4 A full scale, 41.5 mV at 8.3 A.
- Firmware port needed (libraries: Rob Tillaart INA226 or INA226_WE).

## XIAO ESP32-S3 pin plan (from the 14 Nov 2026 research; verify against the Seeed pinout before wiring)
- EMG inputs on A0, A1, A3, A8 (ADC1, so Wi-Fi/BLE do not conflict). INA226 on D4 (SDA) and D5 (SCL). Servo PWM on D9. E-stop input on D10.
- Avoid D2 (strapping pin) and D6/D7 (UART0) for the servo or e-stop. The current sketch uses Arduino-style pin numbers (servo 9, e-stop 2) that need remapping in the port.
- ESP32Servo: `setPeriodHertz(50)` and `attach(pin, 500, 2500)`.
- If the servo is unreliable at a 3.3 V signal, buffer the signal to 5 V (single MOSFET stage or a 74AHCT-type buffer on the 5 V rail).

## Things to measure before wearing it
1. Stall current and torque at 10, 12 and 12.6 V, with the horn clamped.
2. 3.3 V signal reliability across the full range at 12.6 V.
3. Peak bus voltage while back-driving the elbow by hand.
4. The low-voltage cutoff trips at the set voltage and does not trip on servo start, and the fuse blows on a (fused) short.
5. Relay drops out reliably when the pack is low; contacts after stall breaks.
6. Servo case temperature while holding (no duty-cycle rating is published).
7. Pack weight and where it is worn.

## Battery-on-body safety
- Formal guidance (CPSC or the pack seller's documentation) was not retrieved, so find it before first wear.
- Minimum practice: rigid vented enclosure on the chest plate, not against the skin; fuse at the pack +; no charging while worn; charge on a non-flammable surface; never use dented or re-wrapped cells.
