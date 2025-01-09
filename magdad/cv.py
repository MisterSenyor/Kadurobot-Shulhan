import cv2
import numpy as np
from settings import *

class CircularityFilter:
    def __init__(self, lower=0.0, upper=1.5):
        self.bounds = {"lower": lower, "upper": upper}

    def update_lower_bound(self, val):
        self.bounds["lower"] = val / 100.0

    def update_upper_bound(self, val):
        self.bounds["upper"] = val / 100.0

class PointSelector:
    def __init__(self):
        self.points = []

    def mouse_callback(self, event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN and len(self.points) < 4:
            self.points.append((x, y))
            print(f"Point {len(self.points)}: {x}, {y}")
        elif event == cv2.EVENT_RBUTTONDOWN and self.points:
            popped_point = self.points.pop()
            print(f"Removed point: {popped_point}")

    def clear_points(self):
        self.points.clear()

class BallHandler:
    def __init__(self, board_width_mm, board_height_mm):
        self.circularity_filter = CircularityFilter()
        self.point_selector = PointSelector()
        self.transform_matrix = None

        cv2.namedWindow("Settings")
        cv2.createTrackbar("Lower Circularity", "Settings", int(self.circularity_filter.bounds["lower"] * 100), 150, self.circularity_filter.update_lower_bound)
        cv2.createTrackbar("Upper Circularity", "Settings", int(self.circularity_filter.bounds["upper"] * 100), 150, self.circularity_filter.update_upper_bound)

        cv2.namedWindow("Yellow Ball Detection")
        cv2.setMouseCallback("Yellow Ball Detection", self.point_selector.mouse_callback)

        self.board_width_mm = board_width_mm
        self.board_height_mm = board_height_mm

    def calculate_transform_matrix(self):
        if len(self.point_selector.points) == 4:
            warped_plane = np.array([
                [self.board_width_mm, self.board_height_mm],
                [self.board_width_mm, 0],
                [0, 0],
                [0, self.board_height_mm]
            ], dtype="float32")
            points_array = np.array(self.point_selector.points, dtype="float32")
            self.transform_matrix = cv2.getPerspectiveTransform(points_array, warped_plane)
            print("Perspective transformation matrix calculated.")

    def detect_yellow_ball(self, callback=None):
        ret, frame = self.cap.read()
        if not ret:
            print("Failed to grab frame")
            self.close_camera()

        for i, point in enumerate(self.point_selector.points):
            cv2.circle(frame, point, 5, (0, 0, 255), -1)
            text = f"P{i + 1}"
            x, y = self.ensure_on_screen(frame, text, point[0] + 10, point[1] - 10, 0.5, 1)
            cv2.putText(frame, text, (x, y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)

        if len(self.point_selector.points) == 4 and self.transform_matrix is None:
            self.calculate_transform_matrix()

        hsv_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        lower_yellow = np.array([15, 80, 80])
        upper_yellow = np.array([35, 255, 255])
        yellow_mask = cv2.inRange(hsv_frame, lower_yellow, upper_yellow)
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        cleaned_mask = cv2.morphologyEx(yellow_mask, cv2.MORPH_CLOSE, kernel)
        
        contours, _ = cv2.findContours(cleaned_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        best_fit, best_score, ball_position = None, -1, None

        for contour in contours:
            area = cv2.contourArea(contour)
            perimeter = cv2.arcLength(contour, True)
            circularity = 4 * np.pi * (area / (perimeter ** 2)) if perimeter > 0 else 0

            if 500 < area < 5000 and self.circularity_filter.bounds["lower"] <= circularity <= self.circularity_filter.bounds["upper"]:
                mask = np.zeros_like(cleaned_mask)
                cv2.drawContours(mask, [contour], -1, 255, thickness=cv2.FILLED)
                yellowness = cv2.mean(cleaned_mask, mask=mask)[0]
                score = circularity * yellowness

                if score > best_score:
                    best_fit = contour
                    best_score = score

        if best_fit is not None:
            x, y, w, h = cv2.boundingRect(best_fit)
            ball_center = (x + w // 2, y + h // 2)

            if self.transform_matrix is not None:
                ball_position = cv2.perspectiveTransform(
                    np.array([[ball_center]], dtype="float32"), self.transform_matrix
                )[0][0]
            else:
                ball_position = ball_center

            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
            text_score = f"Score: {best_score:.2f}"
            text_pos = f"Pos: ({int(ball_position[0])}, {int(ball_position[1])})" if ball_position else ""
            
            x_score, y_score = self.ensure_on_screen(frame, text_score, x, y - 20, 0.5, 1)
            cv2.putText(frame, text_score, (x_score, y_score), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

            if text_pos:
                x_pos, y_pos = self.ensure_on_screen(frame, text_pos, x, y - 40, 0.5, 1)
                cv2.putText(frame, text_pos, (x_pos, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

            if callback:
                callback(ball_position)

        cv2.imshow("Yellow Ball Detection", frame)
        cv2.imshow("Contours", cv2.drawContours(np.zeros_like(frame), contours, -1, (255, 255, 255), 1))

        if cv2.waitKey(1) & 0xFF == ord('q'):
            self.close_camera()
        
        return ball_position

    def ensure_on_screen(self, frame, text, x, y, font_scale, thickness):
        (text_width, text_height), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, font_scale, thickness)
        frame_height, frame_width = frame.shape[:2]

        if x + text_width > frame_width:
            x = frame_width - text_width - 5
        if y - text_height < 0:
            y = text_height + 5

        return x, y

    def close_camera(self):
        self.cap.release()
        cv2.destroyAllWindows()
