const int stepPin = 5;
const int dirPin = 3;
const int acceleration = 20;
const int maxStepDelay = 400;
const int minStepDelay = 900;
int stepDelay = minStepDelay; // Delay between steps in microseconds
int flag = 0;

void setup() {
  pinMode(stepPin, OUTPUT); // Set step pin as output
  pinMode(dirPin, OUTPUT);  // Set direction pin as output

  digitalWrite(dirPin, HIGH); // Set initial direction
  Serial.begin(9600); // Start serial communication
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
      digitalWrite(dirPin, LOW); // Set initial direction
    }
    else if (command.equals("DOWN")) {
      digitalWrite(dirPin, HIGH); // Set initial direction
    }
    else { 
      int steps = command.toInt();
      stepDelay = minStepDelay;
      for (int i = 0; i < steps; i++) {
          step();
      }
    }

    Serial.print("Hello World! \n");

  }
}
