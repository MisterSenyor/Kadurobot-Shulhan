import random
import cv2
import time
import json
import numpy as np
import requests
from ball_tracker import BallTracker
import ball_cv
import player_cv
import stepper_api
import settings
import serial
from system_logic import SystemLogic

ANG_DELAY = 0.2


class BallTrackingSystem:
    def __init__(self, json_path, video=False):
        self.tracker = BallTracker()
        self.player_handler = player_cv.PlayersDetector()
        self.ball_handler = ball_cv.BallDetector()
        self.json_path = json_path
        self.load_config()
        self.system_logic = SystemLogic(self.table_points, self.aggressive_row, self.middle_row, self.goalkeeper_row)

        self.steppers = self.initialize_steppers()
        self.steppers["linear"][0].reverse = -1
        self.steppers["linear"][1].reverse = 1
        self.steppers["linear"][2].reverse = -1
        self.steppers["angular"][0].reverse = -1
        self.steppers["angular"][1].reverse = 1
        self.steppers["angular"][2].reverse = 1

        self.frame_idx = 0
        self.table_points = None
        self.player_rows = [self.aggressive_row, self.middle_row, self.goalkeeper_row]
        self.prev_moving_mms = None

        self.recording = False
        self.video_writer = None
        self.pausing = video
        if video:
            with open(json_path, 'r') as f:
                json_data = json.load(f)
            self.source = json_data["path"]
        else:
            self.source = 1

    @staticmethod
    def initialize_steppers():
        serials = [serial.Serial(port, baudrate=settings.BAUD_RATE, write_timeout=1) for port in settings.SERIAL_PORTS]
        if len(serials) == 2:
            steppers = {
                "linear": [stepper_api.StepperHandler(serials[0], stepper_type=f"MOT{i}") for i in range(3)],
                "angular": [
                    stepper_api.StepperHandler(serials[1], stepper_type=f"MOT{i}", calibration=settings.ANGULAR_STEPPER)
                    for i in range(3)]
            }
        else:
            steppers = {
                "linear": [stepper_api.StepperHandler(arduino_serial, stepper_type=settings.LINEAR_STEPPER, ) for
                           arduino_serial in serials],
                "angular": [stepper_api.StepperHandler(arduino_serial, stepper_type=settings.ANGULAR_STEPPER) for
                            arduino_serial in serials],
            }
        for arduino in serials:
            arduino.write("RESET\n".encode())
        return steppers

    def start_recording(self, frame):
        self.recording = True
        h, w = frame.shape[:2]
        fourcc = cv2.VideoWriter_fourcc(*"XVID")
        filename = f"tracking_recording_{int(time.time())}.avi"
        self.video_writer = cv2.VideoWriter(filename, fourcc, 20.0, (w, h))
        print(f"⏺️ Started recording to {filename}")

    def stop_recording(self):
        self.recording = False
        if self.video_writer:
            self.video_writer.release()
            self.video_writer = None
            print("⏹️ Stopped recording.")

    def fetch_frame(self):
        if not hasattr(self, "webcam_cap"):
            self.webcam_cap = cv2.VideoCapture(self.source, cv2.CAP_DSHOW)
        ret, frame = self.webcam_cap.read()
        return frame if ret else None

    def load_config(self):
        with open(self.json_path, 'r') as f:
            data = json.load(f)
        self.table_points = data["table_points"]
        self.goalkeeper_row = (data["rows"][4][0], data["rows"][4][1])
        self.middle_row = (data["rows"][2][0], data["rows"][2][1])
        self.aggressive_row = (data["rows"][0][0], data["rows"][0][1])
        self.player_handler.lines = data["rows"][::2]
        self.ball_handler.selected_points = self.table_points
        self.player_handler.selected_points = self.table_points

    def initialize_perspective(self):
        while True:
            frame = self.fetch_frame()
            if frame is not None and frame.shape[0] > 0:
                break
            print("frame is still None")
            time.sleep(0.5)

        self.ball_handler.create_quadrilateral_mask(frame)
        self.ball_handler.calculate_perspective_transform()

    def manage_game(self, frame, coordinates, player_middles):
        line = self.tracker.get_last_line()

        # Loop for all 3 rows
        for i in range(3):
            # Setup
            row = self.player_rows[i]
            angular_stepper = self.steppers["angular"][i]
            linear_stepper = self.steppers["linear"][i]
            transformed_coords = self.ball_handler.apply_perspective_transform(*coordinates)

            # Kick
            angular_movement = self.system_logic.get_angular_movement(transformed_coords, row)
            if angular_movement is not None:
                angular_stepper.move_to_deg(angular_movement)

            # Predict intersection
            prediction = self.system_logic.predict_intersection(line, row)
            if prediction is None:
                continue
            _, trans_pred_y = self.ball_handler.apply_perspective_transform(*prediction)
            target_mm = self.system_logic.get_linear_movement(trans_pred_y,i)
            if target_mm is None:
                continue

            # Calibrate before move
            if player_middles and len(player_middles) > i:
                players_middles_on_row = player_middles[i]
                if len(players_middles_on_row) == 3:
                    first_middle = players_middles_on_row[2]
                    _, transformed_middle_y = self.ball_handler.apply_perspective_transform(*first_middle)
                    if settings.DEBUG:
                        print(f"setting mms according to players position which is {transformed_middle_y}")
                    self.system_logic.current_players_positions[i] = transformed_middle_y
                    linear_stepper.set_mm(transformed_middle_y)
            linear_stepper.move_to_mm(target_mm) # Move

            # DEBUG
            if settings.DEBUG:
                if line is not None:
                    cv2.line(frame, line[0], line[1], (255, 255, 0), 2)
                cv2.circle(frame, (int(prediction[0]), int(prediction[1])), 10, (0, 0, 255), -1)
                if target_mm is not None:
                    print(f"linear movement is: {target_mm}")
                    cv2.putText(frame, f"Current Pos: {self.system_logic.current_players_positions[i]}", (10, 150 + i * 30),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2, cv2.LINE_AA)
                    cv2.putText(frame, f"Linear Movement: {target_mm}", (10, 50 + i * 30),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2, cv2.LINE_AA)
                    cv2.putText(frame, f"Ball Predicted Position: {trans_pred_y}", (10, 100 + i * 30),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2, cv2.LINE_AA)

    def run_tracking_live(self):
        self.initialize_perspective()
        self.ball_handler.create_windows()
        print("🎮 Press 'r' to record, 's' to stop, 'q' to quit.")
        while True:
            self.frame_idx += 1
            frame = self.fetch_frame()
            if frame is None or frame.shape[0] <= 1 or frame.shape[1] <= 1:
                continue

            key = cv2.waitKey(1) & 0xFF
            if key == ord("q"):
                break
            elif key == ord("r") and not self.recording:
                self.start_recording(frame)
            elif key == ord("s") and self.recording:
                self.stop_recording()
            elif key == ord("g"):  # set position to match CV mm
                player_middles = self.player_handler.find_shapes_on_lines(frame)
                first_goalie = player_middles[0][2]
                first_goalie_mm = self.ball_handler.apply_perspective_transform(*first_goalie)
                print(f"{player_middles=}\t{first_goalie_mm=}")
                self.linear_stepper_handler.set_steps(-1 * settings.CV_MM_TO_STEPS(first_goalie_mm[1]))
                time.sleep(0.05)
                self.linear_stepper_handler.move_to_mm(73)
                time.sleep(0.05)
            elif key == ord("z"): # set position to match CV mm
                player_middles = self.player_handler.find_shapes_on_lines(frame)
                first_goalie = player_middles[0][2]
                first_goalie_mm = self.ball_handler.apply_perspective_transform(*first_goalie)
                print(f"{player_middles=}\t{first_goalie_mm=}")
                self.linear_stepper_handler.set_steps(-1 * settings.CV_MM_TO_STEPS(first_goalie_mm[1]))
                time.sleep(0.05)
                self.linear_stepper_handler.move_to_mm(0)
                time.sleep(0.05)
            elif key == ord("t"):
                self.linear_stepper_handler.move_to_steps(-1 * random.randint(90, 620))
                time.sleep(0.5)
                print(f"{first_goalie=}\t{first_goalie_mm=}")
                self.linear_stepper_handler.set_mm(first_goalie_mm[1])
            elif key in [ord("j"), ord("k"), ord("l")]:
                stepper = self.steppers["angular"][[ord("j"), ord("k"), ord("l")].index(key)]
                stepper.set_steps(0)
                stepper.move_to_steps(stepper.reverse * 90)


            coordinates = self.ball_handler.find_ball_location(frame)[:2]
            if coordinates is not None and not None in coordinates:
                self.tracker.update_position(coordinates[:2])
            # play with the number of the frames
            if self.frame_idx % 5 == 0:
                self.frame_idx = 0
                player_middles = self.player_handler.find_shapes_on_lines(frame)
                self.manage_game(frame, coordinates, player_middles)

            if self.recording and self.video_writer:
                self.video_writer.write(frame)

            if settings.DEBUG:
                for row in self.player_rows:
                    cv2.line(frame, row[0], row[1], (0, 255, 0), 2)
                cv2.namedWindow("Ball Tracking", cv2.WINDOW_NORMAL)
                cv2.imshow("Ball Tracking", frame)
            if self.pausing:
                while True:
                    key = cv2.waitKey(1) & 0xFF
                    if key == ord(" "):
                        break
        if self.video_writer:
            self.video_writer.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    json_path = "../data/camera_data.json"

    system = BallTrackingSystem(json_path)
    system.run_tracking_live()
    # system.demo_all_rows_side_to_side()
