import time
from tkinter.constants import RIGHT
import keyboard
import pyfirmata
from settings import RIGHT, LEFT, STEPS_PER_SECOND, CM_PER_STEPS, MAX_VELOCITY
PORT = "COM13"

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

        if keyboard.is_pressed('right'):
            board.digital[2].write(0)
            current_voltage2 = 0

        if keyboard.is_pressed('left'):
            board.digital[2].write(1)
            current_voltage2 = 1
        #print("hi")ggV
        while keyboard.is_pressed('space'):
            print("PRESSED")
            board.digital[5].write(1)  # turn pin 1
            # 3 ON
            time.sleep(1 / STEPS_PER_SECOND)  # wait 1/2 second
            board.digital[5].write(0)  # turn pin 13 OFF
            time.sleep(1 / STEPS_PER_SECOND)  # wait 1/2 second
        while keyboard.is_pressed('tab'):
            board.digital[6].write(1)  # turn pin 1
            # 3 ON
            time.sleep(1 / STEPS_PER_SECOND)  # wait 1/2 second
            board.digital[6].write(0)  # turn pin 13 OFF
            time.sleep(1 / STEPS_PER_SECOND)  # wait 1/2 second
        # if keyboard.is_pressed('V'):
        #     STEPS_PER_SECOND = int(input("Enter the new velocity: ")[1:])
        if keyboard.is_pressed('S'):
            for _ in range(100):
                current_voltage = step(board, 5, 3, STEPS_PER_SECOND, LEFT, current_voltage)
        if keyboard.is_pressed('D'):
            for _ in range(100):
                current_voltage2 = step(board, 6, 2, STEPS_PER_SECOND, RIGHT, current_voltage2)
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
    main()
