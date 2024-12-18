import time
import keyboard
from stepper import Stepper



def main():

    # set up arduino board
    s1 = Stepper(5, 3, steps_per_rev=200, speed_sps=50)

    # start while loop to keep blinking indefinitely
    while True:
        if keyboard.is_pressed('esc'): # stop making the arduino blink if the escape key is pressed
            break
        if keyboard.is_pressed('up'): # stop making the arduino blink if the escape key is pressed
            pass
        if keyboard.is_pressed('down'):
            pass
        print("hi")
        while keyboard.is_pressed('space'):
            s1.target_deg(90)
            time.sleep(5.0)
            s1.target_deg(0)
            time.sleep(5.0)

def

if __name__ == "__main__":
    main()