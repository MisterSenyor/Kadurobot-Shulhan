from pymata4 import pymata4
import time
import keyboard

def main():
    board = pymata4.Pymata4()
    pins = [3, 5]
    num_steps = 5
    steps_per_second = 100
    board.set_pin_mode_stepper(num_steps, pins)

    while True:
        if keyboard.is_pressed('esc'):
            break
        if keyboard.is_pressed('up'):
            board.stepper_write(21, num_steps)
        if keyboard.is_pressed('down'):
            board.stepper_write(21, -num_steps)
        if keyboard.is_pressed('space'):
            steps_per_second += 50
        if keyboard.is_pressed('tab'):
            steps_per_second -= 50

if __name__ == "__main__":
    main()