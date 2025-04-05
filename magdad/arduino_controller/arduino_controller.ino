const int linearStepPin = 5;
const int linearDirPin = 3;
const int angularStepPin = 6;
const int angularDirPin = 7;
int stepPin = linearStepPin;
int dirPin = linearDirPin;
// int stepPin = angularStepPin;
// int dirPin = angularDirPin;
const int acceleration = 20;
const int maxStepDelay = 400;
const int minStepDelay = 900;
int stepDelay = minStepDelay; // Delay between steps in microseconds
int stepCounter = 0;          // Tracks the current step position

void setup() {
  pinMode(linearStepPin, OUTPUT); // Set step pin as output
  pinMode(linearDirPin, OUTPUT);  // Set direction pin as output
  pinMode(angularStepPin, OUTPUT); // Set step pin as output
  pinMode(angularDirPin, OUTPUT);  // Set direction pin as output

  digitalWrite(dirPin, HIGH); // Set initial direction
  Serial.begin(9600); // Start serial communication
  Serial.println("Ready! Send UP, DOWN, or a target step count.");

//  stepPin = angularStepPin;
//  dirPin = angularDirPin;
}

void step() {
  digitalWrite(stepPin, HIGH);
  delayMicroseconds(stepDelay);
  digitalWrite(stepPin, LOW);
  delayMicroseconds(stepDelay);
}

void loop() {
// static int stepPin = linearStepPin;
// static int dirPin = linearDirPin;
  if (Serial.available() > 0) {
    String command = Serial.readStringUntil('\n'); // Read command
    if (command.equals("UP")) {
      digitalWrite(dirPin, LOW); // Set direction to UP
      Serial.println("Direction set to UP");
    } 
    else if (command.equals("DOWN")) {
      digitalWrite(dirPin, HIGH); // Set direction to DOWN
      Serial.println("Direction set to DOWN");
    }
    else if (command.equals("LIN")) {
      stepPin = linearStepPin;
      dirPin = linearDirPin;
    }
    else if (command.equals("ANG")) {
      stepPin = angularStepPin;
      dirPin = angularDirPin;
    }
    else {
      String command = Serial.readStringUntil('\n'); // Read number after s command
      // if (command.charAt(0) == 's') { command = command.substring(1); }
      int target = command.toInt(); // Convert the command to an integer

      if (target != stepCounter) {
        Serial.println(stepCounter);
        Serial.println(target);

        int stepsToRun = target - stepCounter; // Calculate steps needed to reach the target
        int direction = (stepsToRun > 0) ? LOW : HIGH; // Determine direction
        digitalWrite(dirPin, direction);

        stepsToRun = abs(stepsToRun); // Use absolute value for the loop
        Serial.print(stepsToRun);
        while (Serial.available() > 0) {
          Serial.read(); // Read and discard characters
        }
        for (int i = 0; i < stepsToRun; i++) {
          if (Serial.available() > 0) {
            char stopChar = Serial.read(); // Read the character
            if (stopChar == 's') {
              char stopChar = Serial.read(); // empty newline from queue
              break; // Exit the loop
            }
          }
          step();
          stepCounter += (direction == LOW) ? 1 : -1; // Update the step counter
        }

        Serial.println(stepCounter);
      }
    }
  }
}
