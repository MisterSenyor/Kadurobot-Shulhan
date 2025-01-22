const int stepPin = 5;
const int dirPin = 3;
const int acceleration = 20;
const int maxStepDelay = 400;
const int minStepDelay = 900;
int stepDelay = minStepDelay; // Delay between steps in microseconds
int stepCounter = 0;          // Tracks the current step position

void setup() {
  pinMode(stepPin, OUTPUT); // Set step pin as output
  pinMode(dirPin, OUTPUT);  // Set direction pin as output

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

void loop() {
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
    else {
      int target = command.toInt(); // Convert the command to an integer

      if (target != stepCounter) {
        Serial.print("Current step count: ");
        Serial.println(stepCounter);
        Serial.print("Target step count: ");
        Serial.println(target);

        int stepsToRun = target - stepCounter; // Calculate steps needed to reach the target
        int direction = (stepsToRun > 0) ? LOW : HIGH; // Determine direction
        digitalWrite(dirPin, direction);

        stepsToRun = abs(stepsToRun); // Use absolute value for the loop
        Serial.print("Running ");
        Serial.print(stepsToRun);
        Serial.println(" steps. Send 's' to stop.");

        for (int i = 0; i < stepsToRun; i++) {
          
          if (Serial.available() > 0) {
            char stopChar = Serial.read(); // Read the character
            if (stopChar == 's') {
              Serial.println("Stopping steps...");
              break; // Exit the loop
            }
          }
          step();
          stepCounter += (direction == LOW) ? 1 : -1; // Update the step counter
        }

        Serial.print("Steps complete or interrupted. Current step count: ");
        Serial.println(stepCounter);
      } else {
        Serial.println("Step counter already at target value.");
      }
    }
  }
}
