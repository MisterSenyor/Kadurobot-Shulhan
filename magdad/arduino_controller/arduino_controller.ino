const int linearStepPin = 5;
const int linearDirPin = 2;
const int angularStepPin = 6;
const int angularDirPin = 3;
int stepPin = 5;
int dirPin = 2;
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
  step();
}
