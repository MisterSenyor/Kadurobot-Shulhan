#include <AccelStepper.h>

// Define pins for 3 linear motors
#define LIN0_STEP_PIN 5
#define LIN0_DIR_PIN 2

#define LIN1_STEP_PIN 6
#define LIN1_DIR_PIN 3

#define LIN2_STEP_PIN 7
#define LIN2_DIR_PIN 4

#define MAX_SPEED 3000
#define ACCELERATION 50000
#define MAX_TARGET 540
#define MIN_STEPS 80

// Create 3 AccelStepper instances
AccelStepper linearMotors[3] = {
  AccelStepper(AccelStepper::DRIVER, LIN0_STEP_PIN, LIN0_DIR_PIN),
  AccelStepper(AccelStepper::DRIVER, LIN1_STEP_PIN, LIN1_DIR_PIN),
  AccelStepper(AccelStepper::DRIVER, LIN2_STEP_PIN, LIN2_DIR_PIN)
};

void setup() {
  Serial.begin(9600);
  Serial.println("Ready. Send LINx pos (e.g., LIN1 300)");

  // Configure all motors
  for (int i = 0; i < 3; ++i) {
    linearMotors[i].setMaxSpeed(MAX_SPEED);
    linearMotors[i].setAcceleration(ACCELERATION);
  }
}

void loop() {
  if (Serial.available() > 0) {
    String input = Serial.readStringUntil('\n');
    input.trim();

    if (input.startsWith("LIN")) {
      int motorIndex = input.charAt(3) - '0';  // Extract motor index
      if (motorIndex >= 0 && motorIndex < 3) {
        int spaceIndex = input.indexOf(' ');
        if (spaceIndex > 0) {
          int target = input.substring(spaceIndex + 1).toInt();
          target = constrain(target, 0, MAX_TARGET);
          if (abs(target - linearMotors[motorIndex].currentPosition()) > MIN_STEPS) {
            linearMotors[motorIndex].moveTo(target);
            Serial.print("Moving LIN");
            Serial.print(motorIndex);
            Serial.print(" to ");
            Serial.println(target);
          }
        }
      } else {
        Serial.println("Invalid motor index");
      }
    }
  }

  // Run all motors
  for (int i = 0; i < 3; ++i) {
    linearMotors[i].run();
  }
}
