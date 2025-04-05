import time

import keyboard

import magdad.ball_cv as ball_cv
import settings
import magdad.stepper_api as stepper_api
import cv2
import player_cv

THIRD = settings.BOARD_HEIGHT_MM // 3
mouse_coordinates = [100, 100]

def run_blocking(ball_handler, linear_stepper_handler):
    players_offset = 0
    while True:
        frame = ball_handler.get_frame()
        coordinates = ball_handler.run_frame(frame)
        print(f"{coordinates=}")
        print(f"{players_offset=}")
        camera_players_offset = ball_handler.plane_length_to_pixels(players_offset)
        # if camera_players_offset is not None:
        #     cv2.line(frame, (0,200 - camera_players_offset), (2000, 200 - camera_players_offset), (0, 255, 0), 2)
        #     cv2.imshow("Main", frame)
        if coordinates is None:
            quit()
        elif coordinates[1] is None:
            continue
        players_offset = handle_blocking(linear_stepper_handler, players_offset, coordinates)
        # time.sleep(1)

def run_attacking(ball_handler: ball_cv.BallDetector, player_handler: player_cv.PlayersDetector, linear_stepper_handler: stepper_api.StepperHandler):
    pass

def handle_blocking(linear_stepper_handler: stepper_api.StepperHandler, players_offset, coordinates):
    moving_mms = coordinates[1] % THIRD
    # moving_mms = coordinates[1]
    actual_moving_mms = moving_mms - players_offset
    if actual_moving_mms > 0:
        direction = settings.DIR_UP
    else:
        direction = settings.DIR_DOWN
    if abs(actual_moving_mms) < settings.MOVING_THRESHOLD:
        return players_offset
    print("moving")
    players_offset = moving_mms
    linear_stepper_handler.move_to_mm(players_offset)
    return players_offset

def calibration_test(ball_handler: ball_cv.BallDetector, linear_stepper_handler: stepper_api.StepperHandler, dist):
    linear_stepper_handler.move_to_mm(dist, settings.DIR_UP)

def move_to_fractions_test(ball_handler, linear_stepper_handler: stepper_api.StepperHandler, divisor):
    jumps_mm = round((settings.BOARD_HEIGHT_MM - settings.HEIGHT_PADDING_MM) / divisor)
    for _ in range(divisor):
        linear_stepper_handler.move_to_mm(jumps_mm, settings.DIR_UP)

def move_to_mouse_test(ball_handler: ball_cv.BallDetector, linear_stepper_handler: stepper_api.StepperHandler):
    global mouse_coordinates
    def move_to_mouse_test_on_click(event, x, y, flags, param):
        global mouse_coordinates
        if event == cv2.EVENT_LBUTTONDOWN:
            mouse_coordinates = [x, y]
    
    players_offset = 0
    while True:
        frame = ball_handler.get_frame()
        ball_handler.run_frame(frame.copy())
        cv2.setMouseCallback("Main", move_to_mouse_test_on_click, frame)
        cv2.circle(frame, mouse_coordinates, 5, (255, 0, 0), -1)
        x, y = ball_handler.apply_perspective_transform(mouse_coordinates[0], mouse_coordinates[1])
        if x is not None:
            players_offset = handle_blocking(linear_stepper_handler, players_offset, [x,y])
            cv2.putText(frame, f"Mouse at ({int(x)}, {int(y)})", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        cv2.imshow("Main", frame)
            
        key = cv2.waitKey(1) & 0xFF
        if key == ord("q"):  # Quit if 'q' is pressed
            break

def kick_test(linear_stepper_handler: stepper_api.StepperHandler):
    linear_stepper_handler.set_stepper(settings.ANGULAR_STEPPER)
    time.sleep(0.5)
    linear_stepper_handler.move_to_deg(-100)
    time.sleep(0.5)
    linear_stepper_handler.move_to_deg(100)

def main():
    print("starting loop")
    ball_handler = ball_cv.BallDetector()
    player_handler = player_cv.PlayersDetector(camera_index=1, initial_group_threshold=20)
    print("ball handler created")
    linear_stepper_handler = stepper_api.StepperHandler(settings.PORT)
    ball_handler.create_windows()
    cv2.namedWindow("Main", cv2.WINDOW_NORMAL)
    reset = input("Reset? Y\\N\n")
    while not keyboard.is_pressed("z") and reset == "y":
        linear_stepper_handler.move_mm(10, settings.DIR_DOWN)
        time.sleep(0.05)
    
    # calibration_test(ball_handler, linear_stepper_handler, 50)
    # move_to_mouse_test(ball_handler, linear_stepper_handler)
    run_blocking(ball_handler, linear_stepper_handler)
    # kick_test(linear_stepper_handler)


if __name__ == "__main__":
    main()
