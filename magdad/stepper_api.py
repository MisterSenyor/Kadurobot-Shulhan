import time
import keyboard
import pyfirmata
from settings import RIGHT, LEFT, STEPS_PER_SECOND, CM_PER_STEPS, STEP_PIN, DIR_PIN


class StepperHandler:
    def __init__(self, port="COM8"):
        self.board = self.define_board(port)
        self.current_voltage = 0
        self.step_pin = STEP_PIN
        self.dir_pin = DIR_PIN
        self.velocity = STEPS_PER_SECOND
        self.direction = RIGHT

    def define_board(self, port="COM8"):
        self.board = pyfirmata.Arduino(port)
        return self.board

    #
    # def step(board, velocity=1000, direction=RIGHT, current_volt=0):
    #     board.digital[DIR_PIN].write(direction)
    #     time.sleep(1 / velocity)
    #     board.digital[STEP_PIN].write((current_volt + 1) % 2)
    #     return (current_volt + 1) % 2

    def step(self, velocity, direction, current_volt):
        self.board.digital[self.dir_pin].write(direction)
        time.sleep(1 / velocity)
        self.board.digital[self.step_pin].write((current_volt + 1) % 2)
        return (current_volt + 1) % 2

    # def move_centimeters(board, centimeters, steps_per_cm=SPS):
    #     current_voltage = 0
    #     for _ in range(centimeters):
    #         for _ in range(steps_per_cm):
    #             current_voltage = step(board, 100, RIGHT, current_voltage)

    def move_centimeters(self, centimeters, velocity, direction):
        current_voltage = 0
        for _ in range(round(centimeters / CM_PER_STEPS)):
            current_voltage = self.step(velocity, direction, current_voltage)

    def change_direction(self, direction):
        self.board.digital[DIR_PIN].write(direction)
