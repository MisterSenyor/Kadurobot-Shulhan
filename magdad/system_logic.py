import math
import time

import keyboard
import numpy as np
from numpy import argmin

import settings
import stepper_api
import cv2


class SystemLogic:
    def __init__(self, table_points, aggressive_row, middle_row, goalkeeper_row):
        self.table_points = table_points
        self.aggressive_row = aggressive_row
        self.middle_row = middle_row
        self.goalkeeper_row = goalkeeper_row
        self.player_rows = [self.aggressive_row, self.middle_row, self.goalkeeper_row]
        self.current_players_positions = [0, 0, 0]
        self.MIN_KICK_DIST = 0.1
        self.MIN_MOVE_DIST = 10
        self.THIRD = settings.BOARD_WIDTH_MM / 3

    def determine_player_row(self, ball_coordinates):
        ball_x, ball_y = ball_coordinates
        if ball_x < self.THIRD:
            return 0, self.aggressive_row
        elif ball_x < 2 * self.THIRD:
            return 1, self.middle_row
        else:
            return 2, self.goalkeeper_row

    @staticmethod
    def predict_intersection(ball_movement_line, player_row):
        if ball_movement_line is None:
            return None
        (x1, y1), (x2, y2) = ball_movement_line
        (x3, y3) = player_row[0]  # start
        (x4, y4) = player_row[1]  # end

        def ccw(A, B, C):
            return (C[1] - A[1]) * (B[0] - A[0]) > (B[1] - A[1]) * (C[0] - A[0])

        def segments_intersect(A, B, C, D):
            return ccw(A, C, D) != ccw(B, C, D) and ccw(A, B, C) != ccw(A, B, D)

        A, B = (x1, y1), (x2, y2)
        C, D = (x3, y3), (x4, y4)

        if not segments_intersect(A, B, C, D):
            return None

        # Compute intersection point
        def line_intersection(p1, p2, p3, p4):
            """Returns intersection point of lines p1p2 and p3p4"""
            x1, y1 = p1
            x2, y2 = p2
            x3, y3 = p3
            x4, y4 = p4

            denom = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
            if abs(denom) < 1e-6:
                return None  # Lines are parallel

            px = ((x1 * y2 - y1 * x2) * (x3 - x4) - (x1 - x2) * (x3 * y4 - y3 * x4)) / denom
            py = ((x1 * y2 - y1 * x2) * (y3 - y4) - (y1 - y2) * (x3 * y4 - y3 * x4)) / denom
            return (px, py)

        return line_intersection(A, B, C, D)

    @staticmethod
    def is_point_on_segment(line, point, tolerance=1e-6):
        px, py = point
        x1, y1 = line[0]
        x2, y2 = line[1]
        return (min(x1, x2) - tolerance <= px <= max(x1, x2) + tolerance) and \
            (min(y1, y2) - tolerance <= py <= max(y1, y2) + tolerance)

    @staticmethod
    def calculate_distance_ball_to_line(line, ball_coords):
        ball_x, ball_y = ball_coords
        x1, y1 = line[0]
        x2, y2 = line[1]

        # Calculate the distance from the ball to the line segment
        num = abs((y2 - y1) * ball_x - (x2 - x1) * ball_y + x2 * y1 - y2 * x1)
        denom = np.sqrt((y2 - y1) ** 2 + (x2 - x1) ** 2)
        return num / denom ** 2

    @staticmethod
    def closest_endpoint(pred_point, line):
        px, py = pred_point
        sx, sy = line[0]
        ex, ey = line[1]
        dist_start = (px - sx) ** 2 + (py - sy) ** 2
        dist_end = (px - ex) ** 2 + (py - ey) ** 2
        return line[0] if dist_start < dist_end else line[1]

    def get_linear_movement(self, ball_y,
                            i,
                            random=False):
        player_current_position = self.current_players_positions[i]
        # moving_mms = ball_y % ((settings.BOARD_WIDTH_MM - settings.PLAYER_WIDTH_MM / 2) // 3)
        covering_players = []
        for i in range(len(settings.PLAYERS_RANGES)):
            start, end = settings.PLAYERS_RANGES[i]
            if start <= ball_y <= end:
                covering_players.append(i)
        if len(covering_players) == 0:
            print("No covering players")
            return None
        covering_players_location = [
            player_current_position + i * settings.DISTANCE_BETWEEN_PLAYERS_MM for i in
            covering_players]
        print(f"covering players are: {covering_players}")
        chosen_player = argmin(
            [abs(player_location - ball_y) for player_location in covering_players_location])
        print(f"chosen player is at: {covering_players_location[chosen_player]}")
        # check about the half player constant if needed
        moving_mms = player_current_position + ball_y - covering_players_location[
            chosen_player] - settings.HALF_PLAYER_WIDTH_MM
        moving_mms = max(moving_mms, 0)
        if abs(moving_mms - player_current_position) < self.MIN_MOVE_DIST:
            print(f"moving_mms: {moving_mms}, player_current_position: {player_current_position}")
            return None
        print(f"moving_mms: {moving_mms}, player_current_position: {player_current_position}")
        self.current_players_positions[i] = moving_mms
        return moving_mms

    def get_angular_movement(self, ball_coordinates, player_row):
        ball_x, ball_y = ball_coordinates
        distance = self.calculate_distance_ball_to_line(player_row, (ball_x, ball_y))
        if distance > self.MIN_KICK_DIST:
            return None
        return 360
