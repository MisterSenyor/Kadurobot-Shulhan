import serial
import time
import keyboard
from stepper_api import StepperHandler

# Define the serial port and baud rate (ensure these match your Arduino sketch)
serial_port = "COM4"  # Replace with the correct port (e.g., "/dev/ttyUSB0" on Linux)
baud_rate = 9600

# Open serial connection
arduino = serial.Serial(serial_port, baud_rate)
time.sleep(1)  # Wait for the connection to establish
handlers = [StepperHandler(arduino, stepper_type="MOT0"),
            StepperHandler(arduino, stepper_type="MOT1")]
current = handlers[1]
print("Starting stepper motor control...")
count = 0
line = ""
arduino.write("RESET\n".encode())
c = 30
while True:
    try:
        # Command the Arduino to step the motor
        # print("STARTING -----------------")
        if arduino.in_waiting > 0:
            line = arduino.readline().decode("utf-8").strip()
            print("Received: " + line)
        if keyboard.is_pressed("v"):
            print("MOT2")
            current = handlers[1]
            # arduino.write(b"UP\n")
        elif keyboard.is_pressed("c"):
            print("MOT1")
            current = handlers[0]
            # arduino.write(b"DOWN\n")
        elif keyboard.is_pressed("z"):
            # arduino.write(b"s\n100\n")  # Send the "step" command
            current.move_to_mm(c)
            c += 30
            time.sleep(0.5)
        elif keyboard.is_pressed("x"):
            # arduino.write(b"s\n0\n")  # Send the "step" command
            current.move_to_steps(0)
            time.sleep(0.5)
        elif keyboard.is_pressed("q"):
            quit()
        time.sleep(0.05)  # Adjust delay if needed
    except KeyboardInterrupt:
        print("Stopping...")
        break
        
arduino.close()