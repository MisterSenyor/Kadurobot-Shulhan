import serial
import time

# Define the serial port and baud rate (ensure these match your Arduino sketch)
serial_port = "COM13"  # Replace with the correct port (e.g., "/dev/ttyUSB0" on Linux)
baud_rate = 9600

# Open serial connection
arduino = serial.Serial(serial_port, baud_rate)
time.sleep(2)  # Wait for the connection to establish

print("Starting stepper motor control...")

try:
    # Command the Arduino to step the motor
    print("STARTING -----------------")
    time.sleep(5)
    arduino.write(b"100\n")  # Send the "step" command
    while True:
        pass
    # time.sleep(0.01)  # Adjust delay if needed
except KeyboardInterrupt:
    print("Stopping...")
finally:
    arduino.close()