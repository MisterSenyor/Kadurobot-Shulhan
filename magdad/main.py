import time
from tkinter.constants import RIGHT
import keyboard
import pyfirmata
#import cv
from settings import RIGHT, LEFT, STEPS_PER_SECOND, CM_PER_STEPS
import cv
PORT = "COM8"


def main2():
    ball_handler = cv.BallHandler()
    while True:
        print(ball_handler.detect_yellow_ball())

def controller(ball_pos):
    print("CONTROLLING:")
    print(f"{ball_pos=}")

def game_main():
    cv.detect_yellow_ball_real_time(controller)

def main():
    # set up arduino board
    board = pyfirmata.Arduino(PORT)
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
            time.sleep(1 / STEPS_PER_SECOND)  # wait 1/2 second
            board.digital[5].write(0)  # turn pin 13 OFF
            time.sleep(1 / STEPS_PER_SECOND)  # wait 1/2 second
        # if keyboard.is_pressed('V'):
        #     STEPS_PER_SECOND = int(input("Enter the new velocity: ")[1:])
        if keyboard.is_pressed('S'):
            for _ in range(100):
                current_voltage = step(board, 5, 3, STEPS_PER_SECOND, LEFT, current_voltage)
        if keyboard.is_pressed('C'):
            current_voltage += 1
            current_voltage %= 2
        if keyboard.is_pressed('M'):
            move_centimeters(10, board, 5, 3, STEPS_PER_SECOND, LEFT)


def step(board, step_pin, dir_pin, velocity, direction, current_volt):
    board.digital[dir_pin].write(direction)
    time.sleep(1 / velocity)
    board.digital[step_pin].write((current_volt + 1) % 2)
    return (current_volt + 1) % 2


def move_centimeters(centimeters, board, step_pin, dir_pin, velocity, direction):
    current_voltage = 0
    for _ in range(round(centimeters / CM_PER_STEPS)):
        current_voltage = step(board, step_pin, dir_pin, velocity, direction, current_voltage)



if __name__ == "__main__":
    main2()
