import time
from tkinter.constants import RIGHT

import keyboard
import pyfirmata
import cv
import stepper_module

def controller(ball_pos):
    print("CONTROLLING:")
    print(f"{ball_pos=}")

def game_main():
    cv.detect_yellow_ball_real_time(controller)from setuptools.command.easy_install import current_umask

LEFT = 0
RIGHT = 1


def main():
    # set up arduino board
    board = pyfirmata.Arduino('COM8')
    steps_per_second = 100
    current_voltage = 0

    # start while loop to keep blinking indefinitely
    while True:

        if keyboard.is_pressed('esc'):  # stop making the arduino blink if the escape key is pressed
            break
        if keyboard.is_pressed('up'):  # stop making the arduino blink if the escape key is pressed
            board.digital[3].write(1)
            current_voltage = 1
        if keyboard.is_pressed('down'):
            board.digital[3].write(0)
            current_voltage = 0
        #print("hi")
        while keyboard.is_pressed('space'):
            board.digital[5].write(1)  # turn pin 1
            # 3 ON
            time.sleep(1 / steps_per_second)  # wait 1/2 second
            board.digital[5].write(0)  # turn pin 13 OFF
            time.sleep(1 / steps_per_second)  # wait 1/2 second
        if keyboard.is_pressed('V'):
            steps_per_second = int(input("Enter the new velocity: ")[1:])
        if keyboard.is_pressed('S'):
            for _ in range(100):
                current_voltage = step(board, 5, 3, 100, LEFT, current_voltage)
        if keyboard.is_pressed('C'):
            current_voltage += 1
            current_voltage %= 2


def step(board, step_pin, dir_pin, velocity, direction, current_volt):
    board.digital[dir_pin].write(direction)
    time.sleep(1 / velocity)
    board.digital[step_pin].write((current_volt + 1) % 2)
    return (current_volt + 1) % 2


def move_centimeters(centimeters, steps_per_cm, board):
    current_voltage = 0
    for _ in range(centimeters):
        for _ in range(steps_per_cm):
            current_voltage = step(board, 5, 3, 100, RIGHT, current_voltage)



if __name__ == "__main__":
    main()
