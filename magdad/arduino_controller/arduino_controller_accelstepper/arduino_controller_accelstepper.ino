#include <AccelStepper.h>

#define LINEAR_STEP_PIN 5
#define LINEAR_DIR_PIN 2
#define ANGULAR_STEP_PIN 6
#define ANGULAR_DIR_PIN 3

#define MAX_SPEED 3000
#define ACCELERATION 50000
#define MAX_TARGET 540
#define MIN_STEPS 80

// Create AccelStepper instances
AccelStepper linearMotor(AccelStepper::DRIVER, LINEAR_STEP_PIN, LINEAR_DIR_PIN);
AccelStepper angularMotor(AccelStepper::DRIVER, ANGULAR_STEP_PIN, ANGULAR_DIR_PIN);

// Track which motor is active
AccelStepper* activeMotor = &angularMotor;

// Step position trackers
int linearTarget = 0;
int angularTarget = 0;

void setup() {
  Serial.begin(9600);
  Serial.println("AccelStepper Ready. Send LIN or ANG followed by a target position.");

  // Configure motors
  linearMotor.setMaxSpeed(MAX_SPEED);
  linearMotor.setAcceleration(ACCELERATION);
  angularMotor.setMaxSpeed(MAX_SPEED);
  angularMotor.setAcceleration(ACCELERATION);
}

void loop() {
  if (Serial.available() > 0) {
    String input = Serial.readStringUntil('\n');
    input.trim();

    if (input.equalsIgnoreCase("LIN")) {
      activeMotor = &linearMotor;
      Serial.println("Switched to Linear Motor");
    } else if (input.equalsIgnoreCase("ANG")) {
      activeMotor = &angularMotor;
      Serial.println("Switched to Angular Motor");
    } else {
      int target = input.toInt();
      target = constrain(target, 0, MAX_TARGET);
      if (abs(target - activeMotor->currentPosition()) > MIN_STEPS) {
        activeMotor->moveTo(target);
        Serial.print("Moving to ");
        Serial.println(target);
      }
    }
  }
  activeMotor->run();  // Non-blocking stepping
}

// void loop() {
//   activeMotor->setSpeed(2000);  // Positive = forward, negative = backward
//   activeMotor->runSpeed();
// }
