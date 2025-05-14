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
    def __init__(self, json_path, ip_cam_url=None, video=False):
        self.tracker = BallTracker()
        self.player_handler = player_cv.PlayersDetector()
        self.ball_handler = ball_cv.BallDetector()
        self.json_path = json_path
        self.load_config()
        self.system_logic = SystemLogic(self.table_points, self.aggressive_row, self.middle_row, self.goalkeeper_row)
        
        self.steppers = self.initialize_steppers()
        self.linear_stepper_handler = self.steppers["linear"][1]
        self.angular_stepper_handler = self.steppers["angular"][0]
        
        self.frame_idx = 0
        self.table_points = None
        self.current_players_positions = [0, 0, 0]
        self.player_rows = [self.aggressive_row, self.middle_row, self.goalkeeper_row]
        self.prev_moving_mms = None
        
        self.recording = False
        self.pausing = video
        self.ip_cam_url = ip_cam_url
        self.use_ipcam = ip_cam_url is not None
        self.video_writer = None
        if video:
            with open(json_path, 'r') as f:
                json_data = json.load(f)
            self.source = json_data["path"]
        else:
            self.source = 2

    @staticmethod
    def draw_x(frame, center, size=10, color=(0, 0, 255), thickness=2):
        x, y = center
        cv2.line(frame, (x - size, y - size), (x + size, y + size), color, thickness)
        cv2.line(frame, (x - size, y + size), (x + size, y - size), color, thickness)

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
            frame = self.fetch_ipcam_frame() if self.use_ipcam else self.fetch_webcam_frame()
            if frame is not None and frame.shape[0] > 0:
                break
            print("frame is still None")
            time.sleep(0.5)

        self.ball_handler.create_quadrilateral_mask(frame)
        self.ball_handler.calculate_perspective_transform()

    def manage_game(self, frame):
        coordinates = self.tracker.get_position()
        if coordinates is None:
            return
        # self.tracker.update_position(coordinates[0], coordinates[1])
        line = self.tracker.get_last_line()
        if line is not None:
            cv2.line(frame, line[0], line[1], (255, 255, 0), 2)
        
        for i in range(3):
            row = self.player_rows[i]

            angular_stepper = self.steppers["angular"][i]
            angular_movement = self.system_logic.get_angular_movement(coordinates, row)
            if angular_movement is not None:
                angular_stepper.set_steps(0)
                for angle in angular_movement:
                    if i == 2:
                        angle = -angle
                    # angular_stepper.move_to_deg(angle)
                    # time.sleep(ANG_DELAY)
                # angular_stepper.move_to_deg(0)
                # angular_stepper.set_steps(0)
            prediction = self.system_logic.predict_intersection(line, row)
            if prediction is None:
                continue
            if not self.system_logic.is_point_on_segment(row, prediction):
                # prediction = self.system_logic.closest_endpoint(prediction, row)
                continue
            pred_x, pred_y = prediction
            cv2.circle(frame, (int(pred_x), int(pred_y)), 10, (0, 0, 255), -1)
            linear_stepper = self.steppers["linear"][i]

            transformed_prediction = self.ball_handler.apply_perspective_transform(pred_x, pred_y)
            print("transformed prediction is:", transformed_prediction)

            player_middles = self.player_handler.find_shapes_on_lines(frame)
            # debugging - DELETE the false part
            if player_middles and len(player_middles) > i:
                players_middles_on_row = player_middles[i]
                if players_middles_on_row is not None:
                    if len(players_middles_on_row) == 3:
                        first_middle = players_middles_on_row[0]
                        _, transformed_middle_y = self.ball_handler.apply_perspective_transform(first_middle[0],
                                                                                                first_middle[1])
                        print(f"setting mms according to players position which is {transformed_middle_y}")
                        linear_stepper.set_mm(transformed_middle_y)
                        self.current_players_positions[i] = transformed_middle_y
            linear_movement = self.system_logic.get_linear_movement(transformed_prediction,
                                                                    self.current_players_positions[i])
            if linear_movement is not None:
                cv2.putText(frame, f"Current Pos: {self.current_players_positions[i]}", (10, 150 + i * 30),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2, cv2.LINE_AA)
                self.steppers["linear"][i].set_mm(self.current_players_positions[i])
                linear_stepper.move_to_mm(linear_movement)
                # time.sleep(ANG_DELAY)
                print(f"linear movement is: {linear_movement}")
                self.current_players_positions[i] = linear_movement
                # print on frame the linear movement
                cv2.putText(frame, f"Linear Movement: {linear_movement}", (10, 50 + i * 30),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2, cv2.LINE_AA)
                cv2.putText(frame, f"Ball Predicted Position: {transformed_prediction}", (10, 100 + i * 30),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2, cv2.LINE_AA)

                # linear_stepper.move_to_mm(settings.BOARD_WIDTH_MM / 2)
                # self.current_players_positions[i] = settings.BOARD_WIDTH_MM / 2
                # self.steppers["linear"][i].set_mm(self.current_players_positions[i])

    def run_tracking_live(self):
        self.initialize_perspective()
        self.ball_handler.create_windows()
        print("🎮 Press 'r' to record, 's' to stop, 'q' to quit.")
        while True:
            self.frame_idx += 1
            frame = self.fetch_ipcam_frame() if self.use_ipcam else self.fetch_webcam_frame()
            if frame is None or frame.shape[0] <= 1 or frame.shape[1] <= 1:
                continue
            
            coordinates = self.ball_handler.run_frame(frame)
            player_middles = self.player_handler.find_shapes_on_lines(frame)
            for middle in player_middles:
                for point in middle:
                    cv2.circle(frame, point, 5, (255, 0, 0), -1)
            for row in self.player_rows:
                cv2.line(frame, row[0], row[1], (0, 255, 0), 2)
                
            key = cv2.waitKey(1) & 0xFF

            if key == ord("q"):
                break
            elif key == ord("r") and not self.recording:
                self.start_recording(frame)
            elif key == ord("s") and self.recording:
                self.stop_recording()
            elif key == ord("g"): # set position to match CV mm
                first_goalie = player_middles[0][2]
                first_goalie_mm = self.ball_handler.apply_perspective_transform(*first_goalie)
                print(f"{first_goalie=}\t{first_goalie_mm=}")
                self.linear_stepper_handler.set_mm(first_goalie_mm[1])

            coordinates = self.ball_handler.find_ball_location(frame)[:2]
            self.tracker.update_position(coordinates)

            # play with the number of the frames
            if self.frame_idx % 4 == 0:
                self.frame_idx = 0
                self.manage_game(frame)

            if self.recording and self.video_writer:
                self.video_writer.write(frame)

            cv2.namedWindow("Ball Tracking", cv2.WINDOW_NORMAL)
            cv2.imshow("Ball Tracking", frame)
            if self.pausing:
                while True:
                    key = cv2.waitKey(0) & 0xFF
                    if key == ord(' '):  # SPACE key
                        break

        if self.video_writer:
            self.video_writer.release()
        cv2.destroyAllWindows()

    def demo_all_rows_side_to_side(self, sweep_range_mm=100, step_mm=10, delay=0.05):
        """
        Move all three rows side to side with coordinated kicks at each end of the sweep.
        """
        print("⚽ Starting demo: sweeping all rows side to side with kicks...")

        linear_steppers = self.steppers["linear"]
        angular_steppers = self.steppers["angular"]

        while True:
            time.sleep(0.1)
            for direction in [1, -1]:  # 1 = right, -1 = left
                for offset in range(0, sweep_range_mm + 1, step_mm):
                    target_mm = offset if direction == 1 else sweep_range_mm - offset
                    for linear_stepper in linear_steppers:
                        linear_stepper.select()
                        linear_stepper.move_to_mm(target_mm)
                    time.sleep(delay)

                # After reaching one side, kick from all rows
                for angular_stepper in angular_steppers:
                    angular_stepper.select()
                    angular_stepper.move_to_deg(-90)
                    time.sleep(0.3)
                    angular_stepper.move_to_deg(90)
                    time.sleep(0.3)
                    angular_stepper.move_to_deg(0)

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

    def fetch_ipcam_frame(self):
        try:
            response = requests.get(self.ip_cam_url, timeout=1)
            img_array = np.asarray(bytearray(response.content), dtype=np.uint8)
            frame = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
            return frame
        except Exception as e:
            print(f"❌ Failed to fetch IP cam frame: {e}")
            return None

    def fetch_webcam_frame(self):
        if not hasattr(self, "webcam_cap"):
            # self.webcam_cap = cv2.VideoCapture(self.source, cv2.CAP_DSHOW)
            self.webcam_cap = cv2.VideoCapture(1, cv2.CAP_DSHOW)
        ret, frame = self.webcam_cap.read()
        return frame if ret else None


if __name__ == "__main__":
    # json_path = "../data/test3.json"
    json_path = "../data/camera_data.json"
    ip_cam_url = "http://192.168.1.123:8080/shot.jpg"  # Set to None to use USB webcam

    system = BallTrackingSystem(json_path)
    system.run_tracking_live()
    # system.demo_all_rows_side_to_side()
