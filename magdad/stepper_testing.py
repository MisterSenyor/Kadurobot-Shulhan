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
# lin_handlers = [StepperHandler(arduino1, stepper_type="MOT0"),
#                 StepperHandler(arduino1, stepper_type="MOT1"),
#                 StepperHandler(arduino1, stepper_type="MOT2")]
# ang_handlers = [StepperHandler(arduino2, stepper_type="MOT0"),
#                 StepperHandler(arduino2, stepper_type="MOT1"),
#                 StepperHandler(arduino2, stepper_type="MOT2")]
lin_handlers = [StepperHandler(arduino1, stepper_type="MOT0"),
                None,
                None]
ang_handlers = [StepperHandler(arduino2, stepper_type="MOT0"),
                None,
                None]
current_lin = lin_handlers[0]
current_ang = ang_handlers[0]
print("Starting stepper motor control...")
count = 0
line = ""
arduino1.write("RESET\n".encode())
arduino2.write("RESET\n".encode())
c = 90
while True:
    try:
        # Command the Arduino to step the motor
        # print("STARTING -----------------")
        if arduino1.in_waiting > 0:
            line = arduino1.readline().decode("utf-8").strip()
            print("Received: " + line)
        if keyboard.is_pressed("v"):
            print("MOT2")
            current_lin = lin_handlers[1]
            current_ang = ang_handlers[1]
            # arduino.write(b"UP\n")
        elif keyboard.is_pressed("c"):
            print("MOT1")
            current_lin = lin_handlers[0]
            current_ang = ang_handlers[0]
            # arduino.write(b"DOWN\n")

        elif keyboard.is_pressed("x"):
            print("MOT3")
            current_lin = lin_handlers[2]
            current_ang = ang_handlers[2]

        elif keyboard.is_pressed("a"):
            # arduino.write(b"s\n0\n")  # Send the "step" command
            current_lin.move_to_steps(0)
            current_ang.move_to_steps(0)
            time.sleep(0.05)
        elif keyboard.is_pressed("s"):
            # arduino.write(b"s\n100\n")  # Send the "step" command
            # current_lin.move_to_steps(c)
            # time.sleep(0.5)
            # current_ang.move_to_steps(c)
            # time.sleep(0.5)
            current_lin.move_to_steps(0)
            time.sleep(0.2)
            current_lin.move_to_steps(c)
            c += 90
            c = c % 900
            # current_ang.move_to_steps(0)
            time.sleep(0.2)

        elif keyboard.is_pressed("d"):
            current_lin.stop()
            time.sleep(0.05)
        elif keyboard.is_pressed("w"):
            current_ang.move_to_deg(383)
            time.sleep(0.2)
            current_ang.set_steps(0)
            time.sleep(0.2)
        elif keyboard.is_pressed("e"):
            current_ang.move_to_deg(-383)
            time.sleep(0.2)
            current_ang.set_steps(0)
            time.sleep(0.2)
        elif keyboard.is_pressed("p"):
            current_lin.move_to_deg(360)
            time.sleep(0.2)
            current_lin.set_steps(0)
            time.sleep(0.2)
        elif keyboard.is_pressed("f"):
            current_lin.set_mm(0)

        elif keyboard.is_pressed("q"):
            quit()
        time.sleep(0.05)  # Adjust delay if needed
    except KeyboardInterrupt:
        print("Stopping...")
        break

arduino1.close()
