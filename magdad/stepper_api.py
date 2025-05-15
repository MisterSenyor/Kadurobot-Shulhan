import keyboard
import serial
import time
import datetime
from settings import *


class StepperHandler:
    def __init__(self, arduino_serial, stepper_type=LINEAR_STEPPER, calibration=LINEAR_STEPPER, reverse=1):
        self.arduino = arduino_serial
        self.direction = DIR_UP
        self.stepper_type = stepper_type
        self.reverse = reverse
        self.prev_pos = None
        self.last_time = None
        time.sleep(1)  # Wait for the connection to establish
        self.arduino.write(self.direction.encode())
        self.DEG_PER_STEP = DEG_PER_STEP_LIN if calibration == LINEAR_STEPPER else DEG_PER_STEP_ANG

    def select(self):
        self.arduino.write(f's{self.stepper_type}'.encode())

    def stop(self):
        self.arduino.write(f"STOP{self.stepper_type[-1]}\n".encode())
    
    def set_mm(self, mm):
        if DEBUG:
            print(f"SETTING TO {mm}, {MM_TO_STEPS(mm)}-----------------")
        if 0 <= CV_MM_TO_STEPS(mm) <= MAX_TARGET:
            self.prev_pos = CV_MM_TO_STEPS(mm)
            self.arduino.write(f"SET{self.stepper_type[-1]} {self.reverse * CV_MM_TO_STEPS(mm)}\n".encode())

    def set_steps(self, steps):
        if DEBUG:
            print(f"SETTING {self.stepper_type} TO {steps} STEPS-----------------")
        self.prev_pos = steps
        self.arduino.write(f"SET{self.stepper_type[-1]} {steps}\n".encode())
    
    def move_to_mm(self, mm, force=False):
        if DEBUG:
            print(f"MOVING TO {mm}, {MM_TO_STEPS(mm)}-----------------")
        now = datetime.datetime.now()
        mm = CV_MM_TO_STEPS(mm)
        if DEBUG:
            print(f"{now}, {now if self.last_time is None else (now - self.last_time).total_seconds()}")
        if (force or (self.prev_pos is None or (abs(mm - self.prev_pos) > 15)) and (self.last_time is None or (now - self.last_time).total_seconds() > 0.3)):
            if 0 <= mm <= MAX_TARGET:
                self.prev_pos = mm
                self.last_time = now
                self.arduino.write(f"{self.stepper_type} {self.reverse * mm}\n".encode())
        else:
            if DEBUG:
                print("Staying")

    def move_to_steps(self, steps):
        if DEBUG:
            print(f"MOVING TO {steps}-----------------")
        self.prev_pos = steps
        self.arduino.write(f"{self.stepper_type} {steps}\n".encode())
        
    def move_to_deg(self, deg):
        if DEBUG:
            print(f"MOVING TO {deg}-----------------")
        now = datetime.datetime.now()
        if self.last_time is None or (now - self.last_time).total_seconds() > 0.3:
            self.set_steps(0)
            self.last_time = now
            self.arduino.write(f"{self.stepper_type} {self.reverse * round(deg / self.DEG_PER_STEP)}\n".encode())
    
    def set_stepper(self, motor):
        self.arduino.write(motor.encode())
   
    def move_mm(self, mm, direction):
        if DEBUG:
            print(f"MOVING {mm} IN {direction} -----------------")
        if direction != self.direction:
            self.direction = direction
            self.arduino.write(direction.encode())
            time.sleep(0.005)
        self.arduino.write(f"{self.reverse * round(mm / MM_PER_STEP)}\n".encode())
    
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