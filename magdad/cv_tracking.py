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


class BallTrackingSystem:
    def __init__(self, json_path, ip_cam_url=None, video=False):
        self.json_path = json_path
        self.pausing = video
        self.ip_cam_url = ip_cam_url
        self.tracker = BallTracker()
        self.ball_handler = ball_cv.BallDetector()
        # self.player_handler = player_cv.PlayersDetector()
        self.steppers = self.initialize_steppers()
        self.linear_stepper_handler = self.steppers["linear"][0]
        self.angular_stepper_handler = self.steppers["angular"][0]
        self.load_config()
        self.recording = False
        self.video_writer = None
        self.frame_idx = 0
        self.prev_moving_mms = None
        self.use_ipcam = ip_cam_url is not None
        self.linear_stepper_handler.select()
        if video:
            with open(json_path, 'r') as f:
                json_data = json.load(f)
            self.source = json_data["path"]
        else:
            self.source = 2
        self.MIN_KICK_DIST = 100000

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

    def initialize_steppers(self):
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
        self.player_row_start = data["rows"][0][0]
        self.player_row_end = data["rows"][0][1]
        # self.player_handler.lines = data["rows"]
        self.ball_handler.selected_points = self.table_points
        self.ball_handler.calculate_perspective_transform()
        self.player_row_start_mm = self.ball_handler.apply_perspective_transform(self.player_row_start[0], self.player_row_start[1])
        self.player_row_end_mm = self.ball_handler.apply_perspective_transform(self.player_row_end[0], self.player_row_end[1])
        self.player_row_len = round(np.sqrt((self.player_row_end[0] - self.player_row_start[0]) ** 2 + (self.player_row_end[1] - self.player_row_start[1]) ** 2))
        print(f"{self.player_row_len=}")

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
            self.webcam_cap = cv2.VideoCapture(self.source, cv2.CAP_DSHOW)
        ret, frame = self.webcam_cap.read()
        return frame if ret else None

    def initialize_perspective(self):
        while True:
            frame = self.fetch_ipcam_frame() if self.use_ipcam else self.fetch_webcam_frame()
            if frame is not None and frame.shape[0] > 0:
                break
            print("frame is still None")
            time.sleep(0.5)

        cv2.namedWindow("Ball Tracking", cv2.WINDOW_NORMAL)
        self.ball_handler.create_quadrilateral_mask(frame)
        self.ball_handler.calculate_perspective_transform()

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
                transformed_y = min(self.player_row_len, max(0, transformed_y))
                moving_mms = transformed_y % (self.player_row_len // 3)
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

    def is_point_on_segment(self, point, tolerance=1e-6):
        px, py = point
        x1, y1 = self.player_row_start
        x2, y2 = self.player_row_end
        return (min(x1, x2) - tolerance <= px <= max(x1, x2) + tolerance) and \
            (min(y1, y2) - tolerance <= py <= max(y1, y2) + tolerance)

    def closest_endpoint(self, pred_point):
        px, py = pred_point
        sx, sy = self.player_row_start
        ex, ey = self.player_row_end
        dist_start = (px - sx) ** 2 + (py - sy) ** 2
        dist_end = (px - ex) ** 2 + (py - ey) ** 2
        return self.player_row_start if dist_start < dist_end else self.player_row_end

    def draw_x(self, frame, center, size=10, color=(0, 0, 255), thickness=2):
        x, y = center
        cv2.line(frame, (x - size, y - size), (x + size, y + size), color, thickness)
        cv2.line(frame, (x - size, y + size), (x + size, y - size), color, thickness)

    def on_click(self, event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            print(f"CLICK AT {(x, y)} - {self.ball_handler.apply_perspective_transform(x,y)}")


    def run_tracking_live(self):
        self.initialize_perspective()
        self.ball_handler.create_windows()
        print("🎮 Press 'r' to record, 's' to stop, 'q' to quit.")
        while True:
            frame = self.fetch_ipcam_frame() if self.use_ipcam else self.fetch_webcam_frame()
            cv2.setMouseCallback("Ball Tracking", self.on_click, frame)
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
            # elif key == ord("g"):
            #     label = "Recording..." if self.recording else f"Live {self.tracker.get_velocity()}"
            #     cv2.putText(frame, label, (10, 400), cv2.FONT_HERSHEY_SIMPLEX, 1,
            #                 (0, 0, 255) if self.recording else (0, 255, 0), 2)
            elif key == ord("z"): #for ZERO!
                self.linear_stepper_handler.move_to_mm(0)
            elif key == ord("f"): #for FIX!
                self.linear_stepper_handler.move_to_steps(-100)
            elif key == ord("g"): # for GOTEM!
                # self.linear_stepper_handler.stop()
                self.linear_stepper_handler.set_steps(0)
            # elif key == ord("k"):
            #     self.kick()
            #     print("Kicking...")

            coordinates = self.ball_handler.run_frame(frame)
            # player_boxes = self.player_handler.find_shapes_on_lines(frame)
            cv2.line(frame, self.player_row_start, self.player_row_end, (0, 255, 0), 2)
            self.handle_coordinates_logic(frame, coordinates)

            if self.recording and self.video_writer:
                self.video_writer.write(frame)


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

    def calculate_distance_ball_to_line(self, ball_coords):
        ball_x, ball_y = ball_coords
        x1, y1 = self.player_row_start
        x2, y2 = self.player_row_end

        # Calculate the distance from the ball to the line segment
        num = abs((y2 - y1) * ball_x - (x2 - x1) * ball_y + x2 * y1 - y2 * x1)
        denom = np.sqrt((y2 - y1) ** 2 + (x2 - x1) ** 2)
        return num / denom ** 2



if __name__ == "__main__":
    # json_path = "../data/test3.json"
    json_path = "../data/camera_data.json"
    ip_cam_url = "http://192.168.1.123:8080/shot.jpg"  # Set to None to use USB webcam

    # system = BallTrackingSystem(json_path, ip_cam_url=ip_cam_url)
    system = BallTrackingSystem(json_path)
    system.run_tracking_live()
    # system.demo_all_rows_side_to_side()