// Aegis elbow controller, v1.
// STATUS: written, NOT compiled or tested on hardware. Test without a person first (see README.md).
//
// What it does:
//   - Drives the DS51150 elbow servo to a target angle, rate-limited, inside software angle limits.
//   - E-stop input: when the e-stop opens, the servo is detached and the code refuses to move.
//     The hardware e-stop must still cut servo power on its own (this code is a second layer, not the first).
//   - Current limit: reads servo supply current (INA219 on the servo supply line). Over the trip level
//     for CURRENT_TRIP_MS latches a fault and detaches the servo.
//   - Command timeout: if no new command arrives for CMD_TIMEOUT_MS, the target is held (no new motion).
//   - Faults latch. Clear them with "R" only after the e-stop is released and the current reads normal.
//
// Serial commands (115200 baud):
//   A<deg>   set target angle, e.g. "A45"
//   S        print status
//   R        reset fault (refused while e-stop is pressed)
//
// Hardware assumptions (CHECK before wiring):
//   - Servo signal on PIN_SERVO. Servo power is NOT from the MCU; it comes from its own fused supply.
//   - E-stop: normally-closed pushbutton from PIN_ESTOP to GND (INPUT_PULLUP). Released = closed = LOW; pressed = opens = HIGH.
//   - INA219 current sensor in the servo supply's + line, on I2C (default address 0x40).
//   - Angles are joint flexion in degrees, with 0 = extension stop, 90 = flexion stop. Calibrate SERVO_OFFSET_DEG.

#include <Servo.h>
#include <Wire.h>
#include <Adafruit_INA219.h>

// ---------- pins ----------
const uint8_t PIN_SERVO = 9;
const uint8_t PIN_ESTOP = 2;

// ---------- limits (placeholders until load-tested) ----------
const float ANGLE_MIN = 2.0;            // stay inside the printed stops (0 and 90) with margin
const float ANGLE_MAX = 88.0;
const float MAX_RATE_DPS = 60.0;        // max speed, degrees per second
const float SERVO_OFFSET_DEG = 0.0;     // servo horn angle that corresponds to joint 0 deg; calibrate
const float CURRENT_LIMIT_A = 3.0;      // trip level, far below the vendor stall current (7.4 A); set after load tests
const unsigned long CURRENT_TRIP_MS = 200;
const unsigned long CMD_TIMEOUT_MS = 1000;
const unsigned long LOOP_MS = 20;

// ---------- state ----------
Servo elbow;
Adafruit_INA219 ina;
float targetDeg = 0.0;
float currentDeg = 0.0;                 // our model of where the joint is (open loop, no feedback sensor on the servo)
bool attached = false;
bool faultCurrent = false;
bool faultEstopLatched = false;         // set when e-stop was pressed; cleared only by R
unsigned long lastCmdMs = 0;
unsigned long overCurrentSinceMs = 0;
unsigned long lastLoopMs = 0;

bool estopPressed() {
  // Normally-closed button: pressed = the circuit opens = pin reads HIGH with INPUT_PULLUP.
  return digitalRead(PIN_ESTOP) == HIGH;
}

void attachServo() {
  if (!attached) { elbow.attach(PIN_SERVO); attached = true; }
}

void detachServo() {
  if (attached) { elbow.detach(); attached = false; }
}

void writeAngle(float deg) {
  elbow.write((int)round(deg + SERVO_OFFSET_DEG));
}

void setFault(const char* why) {
  detachServo();
  Serial.print("FAULT: "); Serial.println(why);
}

void setup() {
  Serial.begin(115200);
  pinMode(PIN_ESTOP, INPUT_PULLUP);
  Wire.begin();
  if (!ina.begin()) {
    Serial.println("FAULT: INA219 not found. Refusing to run.");
    while (true) { delay(1000); }       // no current sensing = no current limit = do not move
  }
  // Start with the servo detached. Attach only after a deliberate reset with the arm supported.
  detachServo();
  currentDeg = 0.0;
  targetDeg = 0.0;
  lastCmdMs = millis();
  lastLoopMs = millis();
  Serial.println("Aegis controller v1. Send R to arm (only when the e-stop is released).");
}

void handleSerial() {
  while (Serial.available()) {
    char c = Serial.read();
    if (c == 'A' || c == 'a') {
      float v = Serial.parseFloat();
      if (v < ANGLE_MIN) v = ANGLE_MIN;
      if (v > ANGLE_MAX) v = ANGLE_MAX;
      targetDeg = v;
      lastCmdMs = millis();
      Serial.print("target "); Serial.println(targetDeg);
    } else if (c == 'S' || c == 's') {
      Serial.print("angle "); Serial.print(currentDeg);
      Serial.print(" target "); Serial.print(targetDeg);
      Serial.print(" attached "); Serial.print(attached);
      Serial.print(" estopLatched "); Serial.print(faultEstopLatched);
      Serial.print(" faultCurrent "); Serial.print(faultCurrent);
      Serial.print(" mA "); Serial.println(ina.getCurrent_mA());
    } else if (c == 'R' || c == 'r') {
      if (estopPressed()) { Serial.println("Refused: e-stop is pressed."); continue; }
      if (ina.getCurrent_mA() / 1000.0 > CURRENT_LIMIT_A) { Serial.println("Refused: current still high."); continue; }
      faultEstopLatched = false;
      faultCurrent = false;
      // Re-attach at the current modelled angle so the servo does not jump.
      attachServo();
      writeAngle(currentDeg);
      lastCmdMs = millis();
      Serial.println("Reset. Armed at current angle.");
    }
  }
}

void loop() {
  unsigned long now = millis();
  if (now - lastLoopMs < LOOP_MS) return;
  float dt = (now - lastLoopMs) / 1000.0;
  lastLoopMs = now;

  handleSerial();

  // 1. E-stop: latch and cut motion now.
  if (estopPressed()) {
    if (!faultEstopLatched) { faultEstopLatched = true; setFault("e-stop pressed"); }
  }

  // 2. Current limit: must stay over the trip level for CURRENT_TRIP_MS to latch.
  float amps = ina.getCurrent_mA() / 1000.0;
  if (amps > CURRENT_LIMIT_A) {
    if (overCurrentSinceMs == 0) overCurrentSinceMs = now;
    if (!faultCurrent && now - overCurrentSinceMs >= CURRENT_TRIP_MS) {
      faultCurrent = true;
      setFault("over current");
    }
  } else {
    overCurrentSinceMs = 0;
  }

  // 3. Command timeout: hold the current angle, do not drive toward the old target.
  bool timedOut = (now - lastCmdMs) > CMD_TIMEOUT_MS;
  float goal = timedOut ? currentDeg : targetDeg;

  // 4. Motion: only when no fault and attached. Rate-limited toward the goal.
  if (!faultEstopLatched && !faultCurrent && attached) {
    float step = MAX_RATE_DPS * dt;
    float err = goal - currentDeg;
    if (err > step) err = step;
    if (err < -step) err = -step;
    currentDeg += err;
    if (currentDeg < ANGLE_MIN) currentDeg = ANGLE_MIN;
    if (currentDeg > ANGLE_MAX) currentDeg = ANGLE_MAX;
    writeAngle(currentDeg);
  }
}
