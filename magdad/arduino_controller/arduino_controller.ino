const int stepPin = 5;
const int dirPin = 3;
const int stepDelay = 500; // Delay between steps in microseconds
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
    // String command = Serial.readStringUntil('\n'); // Read command
    int steps = Serial.parseInt(); // Read the number
    Serial.print("Hello World! \n");
    for (int i = 0; i < steps; i++) {
        step();
    }
  }
}
