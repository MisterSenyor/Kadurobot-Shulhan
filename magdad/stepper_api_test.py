import serial
import time
from settings import *


class StepperHandler():
    def __init__(self, port):
        self.baud_rate = 9600
        self.arduino = serial.Serial(port, self.baud_rate)
        self.direction = DIR_UP
        time.sleep(2)  # Wait for the connection to establish
        self.arduino.write(self.direction.encode())

    def move_mm(self, mm, direction):
        print(f"MOVING {mm} IN {direction} -----------------")
        if direction != self.direction:
            self.direction = direction
            self.arduino.write(direction.encode())
            time.sleep(0.005)
        self.arduino.write(f"{round(mm / MM_PER_STEPS)}\n".encode())
    
    def quit(self): 
        self.arduino.close()