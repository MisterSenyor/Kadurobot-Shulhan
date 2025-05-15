#include <AccelStepper.h>

// === Angular Stepper Pins ===
#define ANG0_STEP_PIN 5
#define ANG0_DIR_PIN 2

#define ANG1_STEP_PIN 6
#define ANG1_DIR_PIN 3

#define ANG2_STEP_PIN 7
#define ANG2_DIR_PIN 4

// === Motor Settings ===
// #define MAX_SPEED 6000 // good for linear
// #define ACCELERATION 40000  // good for linear
#define MAX_SPEED 6000 // good for angular
#define ACCELERATION 40000  // good for angular
#define MIN_STEPS 30
#define DIR(X) ((X - motor.targetPosition()) / abs(X - motor.targetPosition()))

// === Create 3 Angular Stepper Instances ===
AccelStepper angularMotors[3] = {
  AccelStepper(AccelStepper::DRIVER, ANG0_STEP_PIN, ANG0_DIR_PIN),
  AccelStepper(AccelStepper::DRIVER, ANG1_STEP_PIN, ANG1_DIR_PIN),
  AccelStepper(AccelStepper::DRIVER, ANG2_STEP_PIN, ANG2_DIR_PIN)
};

int reversing[3] = {0, 0, 0};
int targets[3] = {0, 0, 0};
int motorIndex;

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
      motorIndex = input.charAt(3) - '0';
      if (motorIndex >= 0 && motorIndex < 3) {
        int spaceIndex = input.indexOf(' ');
        if (spaceIndex > 0) {
          int target = input.substring(spaceIndex + 1).toInt();
          // Serial.print("Asked to move to ");
          Serial.println(target);
          targets[motorIndex] = target;
          AccelStepper& motor = angularMotors[motorIndex];
          int pos = motor.currentPosition();
          if (motor.isRunning() && ((target < pos && pos < motor.targetPosition()) || (target > pos && pos > motor.targetPosition()))) {
            // Serial.println("Initiating stop (non-blocking)");
            motor.stop();                   // Initiate deceleration
            reversing[motorIndex] = 1;      // Flag for post-stop handling
          }
          else if (abs(target - motor.targetPosition()) > MIN_STEPS) {
          // if (abs(target - motor.targetPosition()) > MIN_STEPS) {
            motor.moveTo(target);
            // Serial.print("Moving ANG");
            // Serial.print(motorIndex);
            // Serial.print(" to ");
            // Serial.println(target);
          }
        }
      } else {
        Serial.println("Invalid angular motor index");
      }
    }
    else if (input.startsWith("RESET")) {
      reset_motors();
    }
    else if (input.startsWith("STOP")) {
      int motorIndex = input.charAt(4) - '0';
      if (motorIndex >= 0 && motorIndex < 3) {
        AccelStepper& motor = angularMotors[motorIndex];
        motor.stop();
      }
      else {
        Serial.println("Invalid angular motor index");
      }
    }
    else if (input.startsWith("SET")) {
      Serial.println(input);
      int motorIndex = input.charAt(3) - '0';
      if (motorIndex >= 0 && motorIndex < 3) {
        int spaceIndex = input.indexOf(' ');
        if (spaceIndex > 0) {
          int pos = input.substring(spaceIndex + 1).toInt();
          AccelStepper& motor = angularMotors[motorIndex];
          motor.setCurrentPosition(pos);
          // Serial.print("Setting MOT");
          // Serial.print(motorIndex);
          // Serial.print(" to ");
          // Serial.println(pos);
        }
      }
      else {
        Serial.println("Invalid angular motor index");
      }
    }
  }

  for (int i = 0; i < 3; ++i) {
      AccelStepper& motor = angularMotors[i];
      motor.run();  // Drive stepper as usual

      if (reversing[i] && !motor.isRunning()) {
        reversing[i] = 0;
        motor.moveTo(targets[i]);  // Now safe to reverse direction
        // Serial.print("Stopped. Now reversing ANG");
        // Serial.print(i);
        // Serial.print(" to ");
        // Serial.println(targets[i]);
      }
  }
}
