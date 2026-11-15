# Firmware

`aegis_controller/aegis_controller.ino`: controller v1 for the Aegis elbow.

**Status: written, not compiled, not tested on hardware.** Do not power the servo from this until the bench tests below pass.

## What it protects against
- **E-stop:** the e-stop pushbutton must cut servo power in hardware. The code latches a fault and detaches the servo when it sees the e-stop pressed, as a second layer.
- **Over-current:** reads servo supply current with an INA219. Over `CURRENT_LIMIT_A` for `CURRENT_TRIP_MS` latches a fault.
- **Command timeout:** if no command arrives for `CMD_TIMEOUT_MS`, the joint holds its angle.
- **Angle limits:** clamps targets to 2° to 88°, inside the printed stops at about 0° and 90°.
- **Rate limit:** moves at most `MAX_RATE_DPS` per second.
- **Faults latch:** they clear only with `R`, and only if the e-stop is released and current reads normal.

## Known gaps (do not rely on these yet)
- The DS51150 has no position feedback, so `currentDeg` is a model from commands, not a measured angle. If the servo stalls, the code can't see it except through current.
- If the e-stop opens and the arm falls, it falls toward the printed extension stop. Verify that on the bench.
- `CURRENT_LIMIT_A`, `MAX_RATE_DPS` and `SERVO_OFFSET_DEG` are placeholders. Set them from measurements.
- No EMG input yet. Commands are typed over serial.
- Not compiled. It needs the `Servo` and `Adafruit INA219` libraries.

## Bench test order (no person in the arm)
1. Power the MCU only. Check the status line prints and the INA219 is found.
2. Press the e-stop: confirm `FAULT: e-stop pressed` and that the servo has no power from the hardware cut.
3. Release it, send `R`, then `A30`. Confirm slow, smooth motion.
4. Hang a light weight, sweep 2° to 88°. Watch the current with `S`.
5. Hold the joint against a stop by hand (stop, don't force it). Confirm the over-current fault latches within `CURRENT_TRIP_MS`.
6. Only then consider a person, with the arm supported and the e-stop in reach.

Every number in this file is a placeholder until step 4 gives you real measurements.


**Note:** the sketch reads current with an INA219. The BOM now specifies an INA226 with a low-value shunt, because an INA219 breakout saturates near 3.2 A and its shunt runs hot at the DS51150 stall current. The firmware has not been ported yet. The port also needs the XIAO ESP32-S3 pin map in `docs/power.md` (the current sketch uses e-stop pin 2, which is a strapping pin on the XIAO) and an ESP32Servo or LEDC servo output. See `docs/power.md`.
