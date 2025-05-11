import time

import keyboard

import cv_v2
import settings
import stepper_api_test
import cv2

def run_kick(players_offset, player_handler, ball_handler, angular_stepper_handler):
    while True:
        frame = ball_handler.get_frame()
        ball_coordinates = ball_handler.run_frame(frame)
        player_coordinates = player_handler.find_shapes_on_lines(frame) #needs to return player positions


        print(f"{ball_coordinates=}")
        print(f"{player_coordinates=}")
        print(f"{players_offset=}")
        if ball_coordinates is None:
            quit()
        elif ball_coordinates[1] is None:
            continue
        if
        players_offset = handle_ball_location(linear_stepper_handler, players_offset, coordinates)