import time

import cv_v2
import settings
import stepper_api_test
import cv2


def main():
    print("starting loop")
    ball_handler = cv_v2.YellowBallDetector()
    print("ball handler created")
    linear_stepper_handler = stepper_api_test.StepperHandler(settings.PORT)
    players_offset = 0
    third = settings.BOARD_HEIGHT_MM // 3
    ball_handler.create_windows()
    cv2.namedWindow("Player Location", cv2.WINDOW_NORMAL)
    while True:
        print("detecting")
        frame = ball_handler.get_frame()
        coordinates = ball_handler.run_frame(frame)
        print(f"{coordinates=}")
        print(f"{players_offset=}")
        camera_players_offset = ball_handler.plane_length_to_pixels(players_offset)
        # if camera_players_offset is not None:
        #     cv2.line(frame, (0,200 - camera_players_offset), (2000, 200 - camera_players_offset), (0, 255, 0), 2)
        #     cv2.imshow("Player Location", frame)
        if coordinates is None:
            quit()
        elif coordinates[1] is None:
            continue
        moving_mms = coordinates[1] % third
        # moving_mms = coordinates[1]
        actual_moving_mms = moving_mms - players_offset
        if actual_moving_mms > 0:
            direction = settings.DIR_DOWN
        else:
            direction = settings.DIR_UP
        print("moving")
        if abs(actual_moving_mms) < settings.MOVING_THRESHOLD:
            continue
        players_offset = moving_mms
        linear_stepper_handler.move_mm(abs(actual_moving_mms), direction)
        time.sleep(1)


if __name__ == "__main__":
    main()
