BOARD_WIDTH_MM = 340
BOARD_HEIGHT_MM = 590
HEIGHT_PADDING_MM = 25 # 25 including both directions
PLAYER_WIDTH_MM = 20
"""
Ran the following code:
for _ in range(100):
    current_voltage = step(board, 5, 3, steps_per_second, LEFT, current_voltage)
and got 19.5 mm movement for steps_per_second = 100
"""
STEPS_PER_SECOND = 10
CM_PER_STEPS = 7.9 / 400
MM_PER_STEP = 79 / 400
DEG_PER_STEP = 360 / 400

MAX_VELOCITY = 100000
VELOCITY = 8000

L_STEP_PIN = 5
L_DIR_PIN = 3
R_STEP_PIN = 6
R_DIR_PIN = 2

# constants for arduino connection
PORT = "COM9"
DIR_UP = "UP\n"
DIR_DOWN = "DOWN\n"
LINEAR_STEPPER = "LIN\n"
ANGULAR_STEPPER = "ANG\n"
TRIPLE_STEPPER_TYPES = [LINEAR_STEPPER, ANGULAR_STEPPER, "TRI\n"]
MOVING_THRESHOLD = 8


BAUD_RATE = 9600

SERIAL_PORTS = ["COM8", "COM9"]
