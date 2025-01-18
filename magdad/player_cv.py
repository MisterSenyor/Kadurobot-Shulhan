import cv2
import numpy as np
from collections import deque

class LineAndBlobDetector:
    def __init__(self, thickness=5, color_range=((0, 50, 50), (10, 255, 255)), max_window_size=5):
        """
        Initialize the detector.

        :param thickness: Expected thickness of the lines to detect.
        :param color_range: HSV range for blob detection (default is for red blobs).
        :param max_window_size: Size of the sliding window for stability.
        """
        self.thickness = thickness
        self.color_range = color_range
        self.cap = cv2.VideoCapture(0)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        self.sliding_window = deque(maxlen=max_window_size)

        # Load the template blob shape
        self.template_blob = cv2.imread("C:\\Users\\TLP-001\\Desktop\\Code\\Kadurobot-Shulhan\\magdad\\template_blob.png", cv2.IMREAD_GRAYSCALE)
        if self.template_blob is None:
            raise FileNotFoundError("Template blob image not found. Ensure 'template_blob.png' is in the working directory.")

    def preprocess_frame(self, frame):
        """
        Convert the frame to grayscale and blur it.
        :param frame: Input frame.
        :return: Preprocessed frame.
        """
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        return blurred

    def detect_lines(self, frame):
        """
        Detect long, straight lines in the frame.
        :param frame: Input frame.
        :return: List of merged lines.
        """
        edges = cv2.Canny(frame, 50, 150, apertureSize=3)
        lines = cv2.HoughLinesP(edges, 1, np.pi / 180, threshold=100, minLineLength=100, maxLineGap=10)

        if lines is None:
            return []

        # Merge lines that appear to be extensions of each other
        merged_lines = []
        for line in lines:
            x1, y1, x2, y2 = line[0]
            new_line = True
            for i, (mx1, my1, mx2, my2) in enumerate(merged_lines):
                if self.are_lines_collinear((x1, y1, x2, y2), (mx1, my1, mx2, my2)):
                    merged_lines[i] = self.merge_lines((x1, y1, x2, y2), (mx1, my1, mx2, my2))
                    new_line = False
                    break
            if new_line:
                merged_lines.append((x1, y1, x2, y2))

        # Group parallel lines as cylindrical shapes
        cylinders = self.group_parallel_lines(merged_lines)

        return cylinders

    def group_parallel_lines(self, lines, proximity_threshold=20, angle_threshold=10):
        """
        Group parallel lines into cylindrical shapes.
        :param lines: List of lines as (x1, y1, x2, y2).
        :param proximity_threshold: Distance between lines to group them.
        :param angle_threshold: Angle difference to consider lines parallel.
        :return: List of grouped lines as cylinders.
        """
        cylinders = []
        used = [False] * len(lines)

        for i, line1 in enumerate(lines):
            if used[i]:
                continue

            group = [line1]
            x1, y1, x2, y2 = line1
            angle1 = np.arctan2(y2 - y1, x2 - x1)

            for j, line2 in enumerate(lines):
                if i == j or used[j]:
                    continue

                x3, y3, x4, y4 = line2
                angle2 = np.arctan2(y4 - y3, x4 - x3)
                angle_diff = np.abs(np.degrees(angle1 - angle2))

                if angle_diff < angle_threshold:
                    distance = np.abs(y3 - y1) if np.abs(x1 - x2) < np.abs(y1 - y2) else np.abs(x3 - x1)
                    if distance < proximity_threshold:
                        group.append(line2)
                        used[j] = True

            cylinders.append(group)

        return cylinders

    @staticmethod
    def are_lines_collinear(line1, line2, angle_threshold=10, distance_threshold=20):
        """
        Check if two lines are collinear.
        :param line1: First line as (x1, y1, x2, y2).
        :param line2: Second line as (x1, y1, x2, y2).
        :param angle_threshold: Angle threshold in degrees.
        :param distance_threshold: Distance threshold in pixels.
        :return: True if lines are collinear, False otherwise.
        """
        x1, y1, x2, y2 = line1
        x3, y3, x4, y4 = line2

        angle1 = np.arctan2(y2 - y1, x2 - x1)
        angle2 = np.arctan2(y4 - y3, x4 - x3)

        angle_diff = np.abs(np.degrees(angle1 - angle2))
        if angle_diff > angle_threshold:
            return False

        # Check if endpoints are close
        if np.linalg.norm([x1 - x3, y1 - y3]) < distance_threshold or \
           np.linalg.norm([x2 - x4, y2 - y4]) < distance_threshold:
            return True

        return False

    @staticmethod
    def merge_lines(line1, line2):
        """
        Merge two collinear lines into one.
        :param line1: First line as (x1, y1, x2, y2).
        :param line2: Second line as (x1, y1, x2, y2).
        :return: Merged line.
        """
        points = np.array([[line1[0], line1[1]], [line1[2], line1[3]],
                           [line2[0], line2[1]], [line2[2], line2[3]]])
        x_coords, y_coords = points[:, 0], points[:, 1]
        return min(x_coords), min(y_coords), max(x_coords), max(y_coords)

    def detect_blobs(self, frame):
        """
        Detect blobs of a specific shape in the frame.
        :param frame: Input frame.
        :return: List of contours matching the template shape.
        """
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        _, thresh = cv2.threshold(blurred, 60, 255, cv2.THRESH_BINARY)

        # Find contours
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        matches = []

        # Match each contour to the template blob shape
        for contour in contours:
            resized_template = cv2.resize(self.template_blob, (50, 50))
            result = cv2.matchShapes(resized_template, contour, cv2.CONTOURS_MATCH_I1, 0.0)
            if result < 0.3:  # Lower values indicate a better match
                matches.append(contour)

        return matches

    def process_frame(self):
        """
        Process a single frame from the camera feed.
        :return: Processed frame with lines and blobs marked.
        """
        ret, frame = self.cap.read()
        if not ret:
            return None

        preprocessed = self.preprocess_frame(frame)
        cylinders = self.detect_lines(preprocessed)
        blobs = self.detect_blobs(frame)

        # Draw lines
        for group in cylinders:
            for x1, y1, x2, y2 in group:
                cv2.line(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)

        # Draw blobs
        for contour in blobs:
            cv2.drawContours(frame, [contour], -1, (0, 0, 255), 2)

        # Add to sliding window for stability
        self.sliding_window.append((cylinders, blobs))

        # Average results from sliding window
        avg_lines = self.average_lines()
        avg_blobs = self.average_blobs()

        # Draw stabilized lines and blobs
        for group in avg_lines:
            for x1, y1, x2, y2 in group:
                cv2.line(frame, (x1, y1), (x2, y2), (255, 0, 0), 2)

        for contour in avg_blobs:
            cv2.drawContours(frame, [contour], -1, (255, 255, 0), 2)

        # Show edge detection window
        edges = cv2.Canny(preprocessed, 50, 150, apertureSize=3)
        cv2.imshow("Edges", edges)

        return frame

    def average_lines(self):
        """
        Average lines over the sliding window.
        :return: List of averaged lines.
        """
        all_lines = [group for window in self.sliding_window for group in window[0]]
        return all_lines  # Placeholder: Implement actual averaging logic

    def average_blobs(self):
        """
        Average blobs over the sliding window.
        :return: List of averaged blobs.
        """
        all_blobs = [blob for window in self.sliding_window for blob in window[1]]
        return all_blobs  # Placeholder: Implement actual averaging logic

    def run(self):
        """
        Start the real-time detection.
        """
        while True:
            frame = self.process_frame()
            if frame is None:
                break

            cv2.imshow("Line and Blob Detection", frame)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        self.cap.release()
        cv2.destroyAllWindows()

# Example usage:
if __name__ == "__main__":
    detector = LineAndBlobDetector()
    detector.run()
