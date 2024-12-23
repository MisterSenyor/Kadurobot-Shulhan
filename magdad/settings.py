BOARD_WIDTH_MM = 590
BOARD_HEIGHT_MM = 340
LEFT = 0
RIGHT = 1
"""
Ran the following code:
for _ in range(100):
    current_voltage = step(board, 5, 3, steps_per_second, LEFT, current_voltage)
and got 19.5 mm movement for steps_per_second = 100
"""
STEPS_PER_SECOND = 100
CM_PER_STEPS = 1.95 / 100