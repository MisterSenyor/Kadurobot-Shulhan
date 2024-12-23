import cv
import settings
import stepper_api


def main():
    ball_handler = cv.BallHandler()
    stepper_handler = stepper_api.StepperHandler(settings.PORT)
    players_offset = 0
    third = settings.BOARD_HEIGHT_MM // 3
    while True:
        coordinates = ball_handler.detect_yellow_ball()
        moving_mms = coordinates[1] % third
        actual_moving_cms = moving_mms - players_offset
        if actual_moving_cms > 0:
            direction = settings.RIGHT
        else:
            direction = settings.LEFT
        players_offset = moving_mms
        stepper_handler.move_centimeters(abs(actual_moving_cms) / 10, settings.VELOCITY, direction)


if __name__ == "__main__":
    main()
