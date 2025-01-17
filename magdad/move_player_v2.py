import time

import cv
import settings
import stepper_api


def main():
    print("starting loop")
    ball_handler = cv.BallHandler()
    for _ in range(4):
        ball_handler.choose_points()
    print("ball handler created")
    linear_stepper_handler = stepper_api.StepperHandler(settings.PORT, settings.L_STEP_PIN, settings.L_DIR_PIN)
    rotational_stepper_handler = stepper_api.StepperHandler(settings.PORT, settings.R_STEP_PIN, settings.R_DIR_PIN)
    players_offset = 0
    third = settings.BOARD_HEIGHT_MM // 3
    while True:
        print("detecting")
        coordinates = ball_handler.detect_yellow_ball()
        print(f"{coordinates=}")
        if coordinates[1] is None:
            continue
        moving_mms = coordinates[1] % third
        #moving_mms = coordinates[1]
        actual_moving_mms = moving_mms - players_offset
        if actual_moving_mms > 0:
            direction = settings.LEFT
        else:
            direction = settings.RIGHT
        players_offset = moving_mms
        print("moving")
        if abs(actual_moving_mms) < settings.MOVING_THRESHOLD:
            continue
        linear_stepper_handler.move_centimeters_vprofile(abs(actual_moving_mms) / 10, settings.VELOCITY, direction)
        #time.sleep(0.5)


if __name__ == "__main__":
    main()
