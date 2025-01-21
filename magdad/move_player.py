import time

import cv_v2
import settings
import stepper_api


def main():
    print("starting loop")
    ball_handler = cv_v2.YellowBallDetector()
    print("ball handler created")
    stepper_handler = stepper_api.StepperHandler(settings.PORT)
    players_offset = 0
    third = settings.BOARD_HEIGHT_MM // 3
    ball_handler.create_windows()
    while True:
        print("detecting")
        frame = ball_handler.get_frame()
        coordinates = ball_handler.run_frame(frame)
        print(f"{coordinates=}")
        if coordinates is None:
            quit()
        elif coordinates[1] is None:
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
        stepper_handler.move_centimeters(abs(actual_moving_mms) / 10, settings.VELOCITY, direction)
        time.sleep(0.5)


if __name__ == "__main__":
    main()
