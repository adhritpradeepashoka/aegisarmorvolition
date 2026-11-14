# Wiring (made in CircuitBench)

![Wiring diagram in CircuitBench](images/wiring-circuitbench.png)

Project file: [`circuitbench/aegis-wiring.circuitbench.json`](circuitbench/aegis-wiring.circuitbench.json)
(open https://circuitbenchlab.onrender.com, then *File, Import project file*).
It is a **concept diagram**, not a tested circuit.

## Connections

| From | To | Why |
|---|---|---|
| Electrodes E+ / E- / REF | BioAmp EXG Pill IN+ / IN- / REF | muscle signal in |
| Pill VCC / GND | Pico 3V3 / GND | 3.3 V supply, common ground |
| Pill OUT | Pico GP26 (A0, ADC) | EMG signal to the controller |
| Pico GP15 | Servo PWM | position command |
| Battery + | Slide switch (common) | the switch is the kill switch in the servo power line |
| Slide switch | Servo V+ | servo power only when the switch is on |
| Battery - | Servo GND and Pico GND | one common ground |

## What the stand-ins mean (CircuitBench has no exact part for these)

| In the diagram | In the real build |
|---|---|
| Raspberry Pi Pico | NPG Lite or the servo controller in `firmware/` |
| One BioAmp EXG Pill and one signal source | several Muscle BioAmp Candy boards on the steel-thread electrodes of the sleeve |
| SG90-style servo at 5 V | DSSERVO DS51150 at 10 to 12.6 V, on its own supply, lead 300 mm |
| 5 V battery | a supply sized for the DS51150's stall current, with a fuse |
| Slide switch | a proper hardware e-stop (22 mm pushbutton) |

Still to do before real use: servo power from its own supply (not from the controller), a fuse, a current limit, and the e-stop cutting servo power in hardware. See `safety.md`.
