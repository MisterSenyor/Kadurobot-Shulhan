#include <AccelStepper.h>

// Pin definitions
const int linearStepPin = 5;
const int linearDirPin = 2;
const int angularStepPin = 6;
const int angularDirPin = 3;

const int maxTarget = 540;
const int minStepDist = 100;

AccelStepper linearMotor(AccelStepper::DRIVER, linearStepPin, linearDirPin);
AccelStepper angularMotor(AccelStepper::DRIVER, angularStepPin, angularDirPin);

AccelStepper* currentMotor = &linearMotor; // Default to linear motor

void setup() {
  Serial.begin(9600);

  // Configure both motors
  linearMotor.setMaxSpeed(1000); // steps/s
  linearMotor.setAcceleration(200); // steps/s^2

  angularMotor.setMaxSpeed(1000);
  angularMotor.setAcceleration(200);

  Serial.println("Ready! Send LIN, ANG, or a number.");
}

void loop() {
  // Run both motors continuously (non-blocking)
  linearMotor.run();
  angularMotor.run();

  if (Serial.available() > 0) {
    String input = Serial.readStringUntil('\n');
    input.trim();

    if (input.equalsIgnoreCase("LIN")) {
      currentMotor = &linearMotor;
      Serial.println("Switched to LINEAR motor");
    } 
    else if (input.equalsIgnoreCase("ANG")) {
      currentMotor = &angularMotor;
      Serial.println("Switched to ANGULAR motor");
    } 
    else {
      int target = input.toInt();
      target = constrain(target, 0, maxTarget);

      if (abs(target - currentMotor->currentPosition()) >= minStepDist) {
        currentMotor->moveTo(target);
        Serial.print("Moving to: ");
        Serial.println(target);
      }
    }
  }
}
