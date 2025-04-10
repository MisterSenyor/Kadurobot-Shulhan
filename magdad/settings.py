BOARD_WIDTH_MM = 590
BOARD_HEIGHT_MM = 340
HEIGHT_PADDING_MM = 25 # 25 including both directions
"""
Ran the following code:
for _ in range(100):
    current_voltage = step(board, 5, 3, steps_per_second, LEFT, current_voltage)
and got 19.5 mm movement for steps_per_second = 100
"""
STEPS_PER_SECOND = 10
CM_PER_STEPS = 1.95 / 100
MM_PER_STEP = 108 / 500
DEG_PER_STEP = 360 / 400

MAX_VELOCITY = 100000
VELOCITY = 8000

L_STEP_PIN = 5
L_DIR_PIN = 3
R_STEP_PIN = 6
R_DIR_PIN = 2

# constants for arduino connection
PORT = "COM13"
DIR_UP = "UP\n"
DIR_DOWN = "DOWN\n"
LINEAR_STEPPER = "LIN\n"
ANGULAR_STEPPER = "ANG\n"

MOVING_THRESHOLD = 8
