import time
import keyboard
import pyfirmata
from stepper import Stepper
from settings import RIGHT, LEFT, STEPS_PER_SECOND, CM_PER_STEPS, MAX_VELOCITY


class StepperHandler:
    def __init__(self, dir_pin, step_pin, port="COM8"):
        self.board = self.define_board(port)
        self._current_voltage = 0
        self.velocity = STEPS_PER_SECOND
        self.direction = RIGHT
        self._acceleration = 20
        self.max_velocity = MAX_VELOCITY
        self.dir_pin = dir_pin
        self.step_pin = step_pin

    def define_board(self, port="COM8"):
        self.board = pyfirmata.Arduino(port)
        return self.board

    def step(self, velocity, direction):
        self.board.digital[self.dir_pin].write(direction)
        time.sleep(1 / velocity)
        self.board.digital[self.step_pin].write((self._current_voltage + 1) % 2)
        self._current_voltage = (self._current_voltage + 1) % 2

    def move_centimeters(self, centimeters, velocity, direction):
        for _ in range(round(centimeters / CM_PER_STEPS)):
            self.step(velocity, direction)

    def change_direction(self, direction):
        self.board.digital[self.dir_pin].write(direction)

    def step_with_vprofile(self, steps, velocity, direction):
        curr_vel = 100
        for i in range(0, steps, self._acceleration):
            self.step(curr_vel, direction)
            if curr_vel < min(self.max_velocity, velocity):
                curr_vel += self._acceleration

    def move_centimeters_vprofile(self, centimeters, velocity, direction):
        self.step_with_vprofile(round(centimeters / CM_PER_STEPS), velocity, direction)
