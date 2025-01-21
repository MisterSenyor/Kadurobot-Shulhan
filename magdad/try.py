import keyboard
from stepper import Stepper
import time

def main():
    s1 = Stepper(5, 3, steps_per_rev=200, speed_sps=50)
    s2 = Stepper(6, 2, steps_per_rev=200, speed_sps=50)
    s1.overwrite_pos(0)
    s2.overwrite_pos(0)
    while True:
        if keyboard.is_pressed('esc'):
            break
        while keyboard.is_pressed('up'):
            s2.dir = 1
            s2.step(50)
        while keyboard.is_pressed('down'):
            s2.dir = 0
            s2.step(50)
        while keyboard.is_pressed('right'):
            s1.dir = 1
            s1.step(50)
        while keyboard.is_pressed('left'):
            s1.dir = 0
            s1.step(50)
        if keyboard.is_pressed('space'):
            s2.steps_per_sec += 50
        if keyboard.is_pressed('tab'):
            s2.steps_per_sec -= 50
        if keyboard.is_pressed('S'):
            s1.steps_per_sec += 50
        if keyboard.is_pressed('D'):
            s1.steps_per_sec -= 50


if __name__ == "__main__":
    main()