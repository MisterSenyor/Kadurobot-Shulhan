#include <AccelStepper.h>

// === Angular Stepper Pins ===
#define ANG0_STEP_PIN 5
#define ANG0_DIR_PIN 2

#define ANG1_STEP_PIN 6
#define ANG1_DIR_PIN 3

#define ANG2_STEP_PIN 7
#define ANG2_DIR_PIN 4

// === Motor Settings ===
#define MAX_SPEED 3000
#define ACCELERATION 50000
#define MAX_TARGET 540
#define MIN_STEPS 80

// === Create 3 Angular Stepper Instances ===
AccelStepper angularMotors[3] = {
  AccelStepper(AccelStepper::DRIVER, ANG0_STEP_PIN, ANG0_DIR_PIN),
  AccelStepper(AccelStepper::DRIVER, ANG1_STEP_PIN, ANG1_DIR_PIN),
  AccelStepper(AccelStepper::DRIVER, ANG2_STEP_PIN, ANG2_DIR_PIN)
};

void setup() {
  Serial.begin(9600);
  Serial.println("Ready. Use ANGx <pos> (e.g., ANG1 300)");

  for (int i = 0; i < 3; ++i) {
    angularMotors[i].setMaxSpeed(MAX_SPEED);
    angularMotors[i].setAcceleration(ACCELERATION);
  }
}

void reset_motors() {
  for (int i = 0; i < 3; ++i) {
    angularMotors[i].setCurrentPosition(0);
  }}

void loop() {
  if (Serial.available() > 0) {
    String input = Serial.readStringUntil('\n');
    input.trim();

    if (input.startsWith("MOT")) {
      int motorIndex = input.charAt(3) - '0';
      if (motorIndex >= 0 && motorIndex < 3) {
        int spaceIndex = input.indexOf(' ');
        if (spaceIndex > 0) {
          int target = input.substring(spaceIndex + 1).toInt();
          AccelStepper& motor = angularMotors[motorIndex];
          if (abs(target - motor.currentPosition()) > MIN_STEPS) {
            motor.moveTo(target);
            Serial.print("Moving ANG");
            Serial.print(motorIndex);
            Serial.print(" to ");
            Serial.println(target);
          }
        }
      } else {
        Serial.println("Invalid angular motor index");
      }
    }
    else if (input.startsWith("RESET")) {
      reset_motors();
    }
  }

  for (int i = 0; i < 3; ++i) {
    angularMotors[i].run();
  }
}
