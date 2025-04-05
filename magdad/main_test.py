import serial
import time
import keyboard

# Define the serial port and baud rate (ensure these match your Arduino sketch)
serial_port = "COM15"  # Replace with the correct port (e.g., "/dev/ttyUSB0" on Linux)
baud_rate = 9600

# Open serial connection
arduino = serial.Serial(serial_port, baud_rate)
time.sleep(2)  # Wait for the connection to establish

print("Starting stepper motor control...")

while True:
    try:
        # Command the Arduino to step the motor
        print("STARTING -----------------")
        if keyboard.is_pressed("up"):
            arduino.write(b"ANG\n")
            # arduino.write(b"UP\n")
        elif keyboard.is_pressed("down"):
            arduino.write(b"LIN\n")
            # arduino.write(b"DOWN\n")
        elif keyboard.is_pressed("z"):
            # arduino.write(b"s\n100\n")  # Send the "step" command
            arduino.write(b"s\n1000\n")  # Send the "step" command
        elif keyboard.is_pressed("x"):
            # arduino.write(b"s\n0\n")  # Send the "step" command
            arduino.write(b"s\n0\n")  # Send the "step" command
        elif keyboard.is_pressed("q"):
            quit()
        time.sleep(0.05)  # Adjust delay if needed
    except KeyboardInterrupt:
        print("Stopping...")
        
arduino.close()