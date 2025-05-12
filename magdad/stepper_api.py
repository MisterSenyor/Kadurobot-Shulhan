import keyboard
import serial
import time
from settings import *


class StepperHandler:
    def __init__(self, arduino_serial, stepper_type=LINEAR_STEPPER):
        self.arduino = arduino_serial
        self.direction = DIR_UP
        self.stepper_type = stepper_type
        time.sleep(2)  # Wait for the connection to establish
        print(f"arduino serial: {self.direction.encode()}")
        self.arduino.write(self.direction.encode())

    def select(self):
        self.arduino.write(f's{self.stepper_type}'.encode())

    def stop(self):
        self.arduino.write(f"STOP{self.stepper_type[-1]}\n".encode())
    
    def set_mm(self, mm):
        print(f"SETTING TO {mm}, {MM_TO_STEPS(mm)}-----------------")
        if 0 <= MM_TO_STEPS(mm) <= MAX_TARGET:
            self.arduino.write(f"SET{self.stepper_type[-1]} {MM_TO_STEPS(mm)}\n".encode())

    def set_steps(self, steps):
        print(f"SETTING TO {steps}, {MM_TO_STEPS(steps)}-----------------")
        if 0 <= MM_TO_STEPS(steps) <= MAX_TARGET:
            self.arduino.write(f"SET{self.stepper_type[-1]} {MM_TO_STEPS(steps)}\n".encode())
    
    def move_to_mm(self, mm):
        print(f"MOVING TO {mm}, {MM_TO_STEPS(mm)}-----------------")
        if 0 <= MM_TO_STEPS(mm) <= MAX_TARGET:
            self.arduino.write(f"{self.stepper_type} {MM_TO_STEPS(mm)}\n".encode())

    def move_to_steps(self, steps):
        print(f"MOVING TO {steps}-----------------")
        self.arduino.write(f"{self.stepper_type} {steps}\n".encode())
        
    def move_to_deg(self, deg):
        # print(f"MOVING TO {deg}-----------------")
        self.arduino.write(f"{self.stepper_type} {round(deg / DEG_PER_STEP)}\n".encode())
    
    def set_stepper(self, motor):
        self.arduino.write(motor.encode())
   
    def move_mm(self, mm, direction):
        print(f"MOVING {mm} IN {direction} -----------------")
        if direction != self.direction:
            self.direction = direction
            self.arduino.write(direction.encode())
            time.sleep(0.005)
        self.arduino.write(f"{round(mm / MM_PER_STEP)}\n".encode())
    
    def quit(self): 
        self.arduino.close()
    
    def move_100_steps(self):
        self.arduino.write(DIR_UP.encode())
        time.sleep(0.1)
        self.arduino.write(b"500\n")
        time.sleep(0.1)
        # self.arduino.write(DIR_UP.encode())
        # time.sleep(0.1)
        # self.arduino.write(b"100\n")
    
    def move_50_steps(self):
        self.arduino.write(DIR_UP.encode())
        while not keyboard.is_pressed("q"):
            time.sleep(1)
            self.arduino.write(b"10\n")

if __name__ == "__main__":
    handler = StepperHandler(PORT)
    handler.move_100_steps()