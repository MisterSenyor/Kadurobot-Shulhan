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


class BallTrackingSystem:
    def __init__(self, json_path, ip_cam_url=None, video=False):
        self.table_points = None
        self.aggressive_row = None
        self.middle_row = None
        self.goalkeeper_row = None
        self.json_path = json_path
        self.pausing = video
        self.ip_cam_url = ip_cam_url
        self.tracker = BallTracker()
        self.ball_handler = ball_cv.BallDetector()
        # self.player_handler = player_cv.PlayersDetector()
        self.steppers = self.initialize_steppers()
        self.linear_stepper_handler = self.steppers["linear"][1]
        self.angular_stepper_handler = self.steppers["angular"][0]
        self.load_config()
        self.player_rows = [self.aggressive_row, self.middle_row, self.goalkeeper_row]
        self.system_logic = SystemLogic(self.table_points, self.aggressive_row, self.middle_row, self.goalkeeper_row)
        self.recording = False
        self.video_writer = None
        self.frame_idx = 0
        self.prev_moving_mms = None
        self.use_ipcam = ip_cam_url is not None
        self.linear_stepper_handler.select()
        self.current_players_positions = [0, 0, 0]
        if video:
            with open(json_path, 'r') as f:
                json_data = json.load(f)
            self.source = json_data["path"]
        else:
            self.source = 2
        self.ANG_DELAY = 0.05

    @staticmethod
    def initialize_steppers():
        serials = [serial.Serial(port, baudrate=settings.BAUD_RATE, write_timeout=1) for port in settings.SERIAL_PORTS]
        if len(serials) == 2:
            steppers = {
                "linear": [stepper_api.StepperHandler(serials[0], stepper_type=f"MOT{i}") for i in range(3)],
                "angular": [stepper_api.StepperHandler(serials[1], stepper_type=f"MOT{i}") for i in range(3)]
            }
        else:
            steppers = {
                "linear": [stepper_api.StepperHandler(arduino_serial, stepper_type=settings.LINEAR_STEPPER) for
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
        # self.player_handler.lines = data["rows"]
        self.ball_handler.selected_points = self.table_points

    def initialize_perspective(self):
        while True:
            frame = self.fetch_ipcam_frame() if self.use_ipcam else self.fetch_webcam_frame()
            if frame is not None and frame.shape[0] > 0:
                break
            print("frame is still None")
            time.sleep(0.5)

        self.ball_handler.create_quadrilateral_mask(frame)
        self.ball_handler.calculate_perspective_transform()

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

    def manage_game(self, frame, coordinates):
        if coordinates is None or coordinates[0] is None or coordinates[1] is None:
            return

        coordinates = self.ball_handler.find_ball_location(frame)[:2]
        if coordinates is None:
            return
        self.tracker.update_position(coordinates[0], coordinates[1])

        line = self.tracker.get_last_line()
        if line is not None:
            cv2.line(frame, line[0], line[1], (255, 255, 0), 2)

        for i in range(3):
            row = self.player_rows[i]
            angular_stepper = self.steppers["angular"][i]
            angular_movement = self.system_logic.get_angular_movement(coordinates, row)
            if angular_movement is not None:
                angular_stepper.select()
                for angle in angular_movement:
                    angular_stepper.move_to_deg(angle)
                    time.sleep(self.ANG_DELAY)
                angular_stepper.move_to_deg(0)
            prediction = self.system_logic.predict_intersection(line, row)
            if prediction is None:
                continue
            if not self.system_logic.is_point_on_segment(row, prediction):
                prediction = self.system_logic.closest_endpoint(prediction, row)
            pred_x, pred_y = prediction
            cv2.circle(frame, (int(pred_x), int(pred_y)), 10, (0, 0, 255), -1)
            linear_stepper = self.steppers["linear"][i]

            transformed_prediction = self.ball_handler.apply_perspective_transform(pred_x, pred_y)
            linear_movement = self.system_logic.get_linear_movement(transformed_prediction,
                                                                    self.current_players_positions[i])
            if linear_movement is not None:
                linear_stepper.select()
                linear_stepper.move_to_mm(linear_movement)
                self.current_players_positions[i] = linear_movement

    @staticmethod
    def draw_x(frame, center, size=10, color=(0, 0, 255), thickness=2):
        x, y = center
        cv2.line(frame, (x - size, y - size), (x + size, y + size), color, thickness)
        cv2.line(frame, (x - size, y + size), (x + size, y - size), color, thickness)

    def run_tracking_live(self):
        self.initialize_perspective()
        self.ball_handler.create_windows()
        print("🎮 Press 'r' to record, 's' to stop, 'q' to quit.")
        while True:
            frame = self.fetch_ipcam_frame() if self.use_ipcam else self.fetch_webcam_frame()
            if frame is None or frame.shape[0] <= 1 or frame.shape[1] <= 1:
                continue

            self.frame_idx += 1
            key = cv2.waitKey(1) & 0xFF

            if key == ord("q"):
                break
            elif key == ord("r") and not self.recording:
                self.start_recording(frame)
            elif key == ord("s") and self.recording:
                self.stop_recording()
            elif key == ord("g"):
                label = "Recording..." if self.recording else f"Live {self.tracker.get_velocity()}"
                cv2.putText(frame, label, (10, 400), cv2.FONT_HERSHEY_SIMPLEX, 1,
                            (0, 0, 255) if self.recording else (0, 255, 0), 2)
            # elif key == ord("k"):
            #     self.kick()
            #     print("Kicking...")

            coordinates = self.ball_handler.run_frame(frame)
            # player_boxes = self.player_handler.find_shapes_on_lines(frame)
            for row in self.player_rows:
                cv2.line(frame, row[0], row[1], (0, 255, 0), 2)
            self.manage_game(frame, coordinates)

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
                    time.sleep(0.1)
                    angular_stepper.move_to_deg(90)
                    time.sleep(0.1)
                    angular_stepper.move_to_deg(0)

        # print("✅ Demo finished.")

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


if __name__ == "__main__":
    # json_path = "../data/test3.json"
    json_path = "../data/camera_data.json"
    ip_cam_url = "http://192.168.1.123:8080/shot.jpg"  # Set to None to use USB webcam

    # system = BallTrackingSystem(json_path, ip_cam_url=ip_cam_url)
    system = BallTrackingSystem(json_path)
    system.run_tracking_live()
    # system.demo_all_rows_side_to_side()

'''
for later





    def kick(self):
        # TIME_DELAY = 0.1
        # self.angular_stepper_handler.select()
        # time.sleep(TIME_DELAY)
        # self.angular_stepper_handler.move_to_deg(-100)
        # time.sleep(TIME_DELAY)
        # self.angular_stepper_handler.move_to_deg(100)
        # time.sleep(TIME_DELAY)
        # self.angular_stepper_handler.move_to_deg(0)
        # time.sleep(TIME_DELAY)
        # self.linear_stepper_handler.select()
        # coordinates = self.ball_handler.find_ball_location(frame)
        pass

    def spin360(self):
        self.angular_stepper_handler.select()
        time.sleep(0.05)
        self.angular_stepper_handler.move_to_deg(-360)
        time.sleep(0.05)
        self.angular_stepper_handler.move_to_deg(360)
        self.linear_stepper_handler.select()

'''

'''
removed







    def handle_coordinates_logic(self, frame, coordinates):
        if coordinates is None or coordinates[0] is None or coordinates[1] is None:
            return

        coordinates = self.ball_handler.find_ball_location(frame)
        self.tracker.update_position(coordinates[0], coordinates[1])

        line = self.tracker.get_last_line()
        if line is not None:
            cv2.line(frame, line[0], line[1], (255, 255, 0), 2)


        prediction = self.system_logic.predict_intersection(line, )
        if prediction is None:
            return
        pred_x, pred_y = prediction
        if self.is_point_on_segment((pred_x, pred_y)):
            cv2.circle(frame, (int(pred_x), int(pred_y)), 10, (0, 0, 255), -1)
            transformed_point = self.ball_handler.apply_perspective_transform(pred_x, pred_y)
            # key = cv2.waitKey(1) & 0xFF

            # if key == ord("g")
            if transformed_point.any():
                transformed_x, transformed_y = transformed_point
                moving_mms = transformed_y % ((settings.BOARD_WIDTH_MM - settings.PLAYER_WIDTH_MM) // 3)
                if self.prev_moving_mms is None or abs(moving_mms - self.prev_moving_mms) > 10:
                    self.linear_stepper_handler.move_to_mm(moving_mms)
                    self.prev_moving_mms = moving_mms
                # if ball is close enough - kick
                # first calculate distance
                distance = self.calculate_distance_ball_to_line((transformed_x, transformed_y))
                if distance < self.MIN_KICK_DIST:
                    self.kick()
                    print("Kicking...")
        else:
            closest = self.closest_endpoint((pred_x, pred_y))
            self.draw_x(frame, closest, size=15, color=(255, 0, 0), thickness=2)



'''


def handle_coordinates_logic(self, frame, coordinates):
    if coordinates is None or coordinates[0] is None or coordinates[1] is None:
        return

    coordinates = self.ball_handler.find_ball_location(frame)
    self.tracker.update_position(coordinates[0], coordinates[1])

    line = self.tracker.get_last_line()
    if line is not None:
        cv2.line(frame, line[0], line[1], (255, 255, 0), 2)

    # distance = self.calculate_distance_ball_to_line(
    #     self.ball_handler.apply_perspective_transform(coordinates[0], coordinates[1]))
    # if not random.randint(0, 1000):  # Adjust the threshold as needed
    #     self.kick()
    #     print("trying to kick")

    prediction = self.predict_intersection()
    if prediction is None:
        return
    pred_x, pred_y = prediction
    if self.is_point_on_segment((pred_x, pred_y)):
        cv2.circle(frame, (int(pred_x), int(pred_y)), 10, (0, 0, 255), -1)
        transformed_point = self.ball_handler.apply_perspective_transform(pred_x, pred_y)
        # key = cv2.waitKey(1) & 0xFF

        # if key == ord("g")
        if transformed_point.any():
            transformed_x, transformed_y = transformed_point
            moving_mms = transformed_y % ((settings.BOARD_WIDTH_MM - settings.PLAYER_WIDTH_MM) // 3)
            if self.prev_moving_mms is None or abs(moving_mms - self.prev_moving_mms) > 10:
                self.linear_stepper_handler.move_to_mm(moving_mms)
                self.prev_moving_mms = moving_mms
            # if ball is close enough - kick
            # first calculate distance```````````````
            distance = self.calculate_distance_ball_to_line((transformed_x, transformed_y))
            if distance < self.MIN_KICK_DIST:
                self.kick()
                print("Kicking...")
    else:
        closest = self.closest_endpoint((pred_x, pred_y))
        self.draw_x(frame, closest, size=15, color=(255, 0, 0), thickness=2)

def predict_intersection(self):
    line = self.tracker.get_last_line()
    if line is None:
        return None

    (x1, y1), (x2, y2) = line
    (x3, y3) = self.player_row_start
    (x4, y4) = self.player_row_end

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

