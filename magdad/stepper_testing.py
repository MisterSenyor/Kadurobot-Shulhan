import serial
import time
import keyboard
from stepper_api import StepperHandler
import settings

# Define the serial port and baud rate (ensure these match your Arduino sketch)
serial_port1 = settings.SERIAL_PORTS[0]  # Replace with the correct port (e.g., "/dev/ttyUSB0" on Linux)
serial_port2 = settings.SERIAL_PORTS[1]  # Replace with the correct port (e.g., "/dev/ttyUSB0" on Linux)
baud_rate = 9600

# Open serial connection
arduino1 = serial.Serial(serial_port1, baud_rate)
arduino2 = serial.Serial(serial_port2, baud_rate)
time.sleep(1)  # Wait for the connection to establish
lin_handlers = [StepperHandler(arduino1, stepper_type="MOT0"),
                StepperHandler(arduino1, stepper_type="MOT1"),
                StepperHandler(arduino1, stepper_type="MOT2")]
ang_handlers = [StepperHandler(arduino2, stepper_type="MOT0"),
                StepperHandler(arduino2, stepper_type="MOT1"),
                StepperHandler(arduino2, stepper_type="MOT2")]
current_lin = lin_handlers[0]
current_ang = ang_handlers[0]
print("Starting stepper motor control...")
arduino1.write("RESET\n".encode())
arduino2.write("RESET\n".encode())

while True:
    try:
        if arduino1.in_waiting > 0:
            line = arduino1.readline().decode("utf-8").strip()
            print("Received: " + line)
            
        if keyboard.is_pressed("z"):
            print("MOT1")
            current_lin = lin_handlers[0]
            current_ang = ang_handlers[0]
            
        elif keyboard.is_pressed("x"):
            print("MOT2")
            current_lin = lin_handlers[1]
            current_ang = ang_handlers[1]

        elif keyboard.is_pressed("c"):
            print("MOT3")
            current_lin = lin_handlers[2]
            current_ang = ang_handlers[2]

        elif keyboard.is_pressed("a"):
            current_lin.move_to_steps(0)
            current_ang.move_to_steps(0)
            time.sleep(0.05)
        
        elif keyboard.is_pressed("s"):
            current_lin.move_to_steps(200)
            # current_ang.set_steps(0)
            time.sleep(0.05)
            current_ang.move_to_deg(360)

        elif keyboard.is_pressed("d"):
            current_lin.set_steps(0)

        elif keyboard.is_pressed("q"):
            quit()
        time.sleep(0.05)  # Adjust delay if needed
    except KeyboardInterrupt:
        print("Stopping...")
        break

arduino1.close()
