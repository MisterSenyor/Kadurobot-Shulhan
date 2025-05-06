const int linearStepPin = 5;
const int linearDirPin = 2;
const int angularStepPin = 6;
const int angularDirPin = 3;
int stepPin = angularStepPin;
int dirPin = angularDirPin;
// int stepPin = angularStepPin;
// int dirPin = angularDirPin;
const int acceleration = 2;
const int minStepDelay = 500;

const int maxStepDelay = 700;
int stepDelay = maxStepDelay; // Delay between steps in microseconds
int stepCounter = 0;          // Tracks the current step position

void setup() {
  pinMode(linearStepPin, OUTPUT); // Set step pin as output
  pinMode(linearDirPin, OUTPUT);  // Set direction pin as output
  pinMode(angularStepPin, OUTPUT); // Set step pin as output
  pinMode(angularDirPin, OUTPUT);  // Set direction pin as output

  digitalWrite(dirPin, HIGH); // Set initial direction
  Serial.begin(9600); // Start serial communication
  Serial.println("Ready! Send UP, DOWN, or a target step count.");
}

void step() {
  digitalWrite(stepPin, HIGH);
  delayMicroseconds(stepDelay);
  digitalWrite(stepPin, LOW);
  delayMicroseconds(stepDelay);
}

void stepToTargetConstant(int target) {
  if (target != stepCounter) {
    Serial.println(stepCounter);
    Serial.println(target);

    int stepsToRun = target - stepCounter; // Calculate steps needed to reach the target
    int direction = (stepsToRun > 0) ? LOW : HIGH; // Determine direction
    digitalWrite(dirPin, direction);

    stepsToRun = abs(stepsToRun); // Use absolute value for the loop
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
      // Serial.println("Running step");
      step();
      stepCounter += (direction == LOW) ? 1 : -1; // Update the step counter
    }

    // Serial.println(stepCounter);
  }
}

void stepToTargetArticle(int target) {
  long stepsToGo = target - stepCounter;
  int direction = (stepsToGo > 0) ? LOW : HIGH;
  digitalWrite(dirPin, direction);
  stepsToGo = abs(stepsToGo);

  float a = acceleration; // in steps/s²

  float c0 = 0.676 * sqrt(2.0 / a) * 1000.0; // Initial delay in µs
  float cn = c0;
  float n = 0;

  for (int i = 0; i < stepsToGo; i++) {
    if (Serial.available() > 0) {
      char stopChar = Serial.read(); // Read the character
      if (stopChar == 's') {
        char stopChar = Serial.read(); // empty newline from queue
        break; // Exit the loop
      }
    }
    stepDelay = (int)cn;
    step();
    stepCounter += (direction == LOW) ? 1 : -1;

    if (cn > minStepDelay) {
      // Acceleration phase
      n++;
      cn = cn - (2.0 * cn) / (4.0 * n + 1);
    } else {
      // Cruising at constant speed
      cn = minStepDelay;
    }
  }
}


void loop() {
  if (Serial.available() > 0) {
    String command = Serial.readStringUntil('\n'); // Read command
      if (command.equals("LIN")) {
      stepPin = linearStepPin;
      dirPin = linearDirPin;
      Serial.println(command);
    }
    else if (command.equals("ANG")) {
      stepPin = angularStepPin;
      dirPin = angularDirPin;
    }
    else {
      String command = Serial.readStringUntil('\n'); // Read number after s command
      Serial.println(command);
      int target = command.toInt(); // Convert the command to an integer

      stepToTargetArticle(target);
      
    }
  }
}

// void loop() {
//   if (Serial.available() > 0) {
//     String command = Serial.readStringUntil('\n'); // Read command
//     command = Serial.readStringUntil('\n'); // Read number after s command
//     Serial.println(command);
//     while (true) {
//       step();
//     }
//   }
// }

// void loop() {
//  step();
//  }
