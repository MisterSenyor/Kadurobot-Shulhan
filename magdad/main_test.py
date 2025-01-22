import serial
import time
import keyboard

# Define the serial port and baud rate (ensure these match your Arduino sketch)
serial_port = "COM13"  # Replace with the correct port (e.g., "/dev/ttyUSB0" on Linux)
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
            arduino.write(b"UP\n")
        elif keyboard.is_pressed("down"):
            arduino.write(b"DOWN\n")
        elif keyboard.is_pressed("z"):
            arduino.write(b"10\n")  # Send the "step" command
        time.sleep(0.01)  # Adjust delay if needed
    except KeyboardInterrupt:
        print("Stopping...")
        
arduino.close()