import time
import keyboard
import pyfirmata


def main():

    # set up arduino board
    board = pyfirmata.Arduino('COM8')
    steps_per_second = 100

    # start while loop to keep blinking indefinitely
    while True:

        if keyboard.is_pressed('esc'): # stop making the arduino blink if the escape key is pressed
            break
        if keyboard.is_pressed('up'): # stop making the arduino blink if the escape key is pressed
            board.digital[3].write(1)
        if keyboard.is_pressed('down'):
            board.digital[3].write(0)
        print("hi")
        while keyboard.is_pressed('space'):
            board.digital[5].write(1)  # turn pin 1
            # 3 ON
            time.sleep(1 / steps_per_second)  # wait 1/2 second
            board.digital[5].write(0)  # turn pin 13 OFF
            time.sleep(1 / steps_per_second)  # wait 1/2 second
        if keyboard.is_pressed('V'):
            steps_per_second = int(input("Enter the new velocity: "))


if __name__ == "__main__":
    main()