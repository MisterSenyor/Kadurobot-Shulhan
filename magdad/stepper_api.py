import time
import keyboard
import pyfirmata

LEFT = 0
RIGHT = 1
DIR_PIN = 3
STEP_PIN = 5
SPS = 100


def define_board(port="COM8"):
    board = pyfirmata.Arduino(port)
    return board


def step(board, velocity=1000, direction=RIGHT, current_volt=0):
    board.digital[DIR_PIN].write(direction)
    time.sleep(1 / velocity)
    board.digital[STEP_PIN].write((current_volt + 1) % 2)
    return (current_volt + 1) % 2


def move_centimeters(board, centimeters, steps_per_cm=SPS):
    current_voltage = 0
    for _ in range(centimeters):
        for _ in range(steps_per_cm):
            current_voltage = step(board, 100, RIGHT, current_voltage)


def change_direction(board, direction):
    board.digital[DIR_PIN].write(direction)
