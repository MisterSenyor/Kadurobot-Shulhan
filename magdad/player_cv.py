import time
import cv2
import numpy as np
import json

# import magdad.ball_cv as ball_cv, settings, magdad.stepper_api as stepper_api

import ball_cv
import stepper_api

mouse_coordinates = [100, 100]


class PlayersDetector:
    """
    Class for detecting shapes intersecting with lines in a live video feed.
    """

    def __init__(self, camera_index=0, initial_group_threshold=20):
        """
        Initialize the YellowBallDetector.
        @param camera_index: Index of the camera (default is 0 for the primary camera).
        @param initial_ball_radius: Initial radius of the ball in pixels.
        """
        self.ball_handler = ball_cv.BallDetector()
        self.ball_handler.create_windows()
        self.camera_index = camera_index
        self.group_threshold = initial_group_threshold
        self.min_area = 5
        self.cap = cv2.VideoCapture(camera_index, cv2.CAP_DSHOW)  # Use CAP_DSHOW for faster loading on Windows

        # HSV range for blue color
        self.lower_blue = np.array([43, 150, 255])  # Default lower bound
        self.upper_blue = np.array([54, 245, 255])  # Default upper bound

        # Lines defined by middle mouse clicks
        self.lines = []

        # Load preset values if available
        self.load_hsv_values()

    def find_shapes_on_lines(self, frame):
        global mouse_coordinates
        """
        Detect and process shapes that intersect with user-defined lines.
        Groups nearby contours into single bounding boxes if within a defined distance and ensures
        only rectangles that intersect with marked lines are displayed.
        @param frame: Current frame from the video feed.
        @param grouping_distance: Maximum distance between contours to be grouped together.
        """
        hsv_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(hsv_frame, self.lower_blue, self.upper_blue)

        # Find contours in the mask
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # Group contours based on proximity
        bounding_boxes = []
        for contour in contours:
            if cv2.contourArea(contour) < 50:  # Ignore small contours
                continue

            # Get bounding box for the current contour
            x, y, w, h = cv2.boundingRect(contour)
            box = (x, y, x + w, y + h)

            # Check if this box can be merged with existing groups
            merged = False
            for i, group in enumerate(bounding_boxes):
                gx1, gy1, gx2, gy2 = group
                if abs(x - gx2) <= self.group_threshold and abs(y - gy2) <= self.group_threshold:
                    # Merge boxes
                    bounding_boxes[i] = (
                        min(gx1, x), min(gy1, y),
                        max(gx2, x + w), max(gy2, y + h)
                    )
                    merged = True
                    break

            if not merged:
                bounding_boxes.append(box)

        # Filter bounding boxes that intersect with any marked line
        valid_boxes = []
        for box in bounding_boxes:
            x1, y1, x2, y2 = box
            for line in self.lines:
                if len(line) < 4:
                    continue
                lx1, ly1, lx2, ly2 = line
                if self.rect_intersects_line(x1, y1, x2, y2, lx1, ly1, lx2, ly2):
                    # Determine the bounds of the square
                    r = 15
                    square_min_x = min(x1, x2)
                    square_max_x = max(x1, x2)
                    square_min_y = min(y1, y2)
                    square_max_y = max(y1, y2)

                    # Closest point in the square to the circle center
                    closest_x = max(square_min_x, min(mouse_coordinates[0], square_max_x))
                    closest_y = max(square_min_y, min(mouse_coordinates[1], square_max_y))

                    # Check distance from the closest point to the circle's center
                    distance_squared = (closest_x - mouse_coordinates[0]) ** 2 + (closest_y - mouse_coordinates[1]) ** 2
                    if distance_squared <= r ** 2:
                        mouse_coordinates = [100, 100]
                        self.kick()
                    valid_boxes.append(box)
                    break

        # Draw lines and valid bounding boxes
        for line in self.lines:
            if len(line) < 4:
                continue
            x1, y1, x2, y2 = line
            cv2.line(frame, (x1, y1), (x2, y2), (0, 0, 255), 2)  # Draw the line

        for contour in contours:
            cv2.drawContours(frame, [contour], -1, (0, 255, 0), 2)  # Draw individual contours

        for box in valid_boxes:
            x1, y1, x2, y2 = box
            cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 0, 0), 2)  # Draw valid bounding boxes

        cv2.imshow("Mask", mask)
        processed_frame = cv2.bitwise_and(frame, frame, mask=mask)
        cv2.imshow("Processed", processed_frame)

        return valid_boxes

    def kick(self):
        linear_stepper_handler = stepper_api.StepperHandler(settings.PORT)
        linear_stepper_handler.set_stepper(settings.ANGULAR_STEPPER)
        time.sleep(0.5)
        linear_stepper_handler.move_to_deg(-60)
        time.sleep(0.5)
        linear_stepper_handler.move_to_deg(60)

    def rect_intersects_line(self, x1, y1, x2, y2, lx1, ly1, lx2, ly2):
        """
        Check if a rectangle intersects with a line.
        @param x1, y1, x2, y2: Rectangle coordinates (top-left and bottom-right).
        @param lx1, ly1, lx2, ly2: Line start and end coordinates.
        @return: True if the rectangle intersects with the line, False otherwise.
        """
        rect_lines = [
            ((x1, y1), (x2, y1)),  # Top edge
            ((x2, y1), (x2, y2)),  # Right edge
            ((x2, y2), (x1, y2)),  # Bottom edge
            ((x1, y2), (x1, y1)),  # Left edge
        ]

        for rect_line in rect_lines:
            if self.line_intersects(lx1, ly1, lx2, ly2, *rect_line[0], *rect_line[1]):
                return True
        return False

    def line_intersects(self, x1, y1, x2, y2, x3, y3, x4, y4):
        """
        Check if two line segments intersect.
        Uses the cross product method to detect intersection.
        @param x1, y1, x2, y2: Endpoints of the first line.
        @param x3, y3, x4, y4: Endpoints of the second line.
        @return: True if the lines intersect, False otherwise.
        """

        def ccw(a, b, c):
            return (c[1] - a[1]) * (b[0] - a[0]) > (b[1] - a[1]) * (c[0] - a[0])

        p1, p2 = (x1, y1), (x2, y2)
        p3, p4 = (x3, y3), (x4, y4)
        return ccw(p1, p3, p4) != ccw(p2, p3, p4) and ccw(p1, p2, p3) != ccw(p1, p2, p4)

    @staticmethod
    def is_point_on_line(point, line, tolerance=5):
        """
        Check if a point lies on a line segment within a tolerance.
        @param point: Tuple (x, y) of the point to check.
        @param line: Tuple (x1, y1, x2, y2) of the line segment.
        @param tolerance: Distance tolerance for considering a point on the line.
        @return: True if the point is on the line, False otherwise.
        """
        x, y = point
        x1, y1, x2, y2 = line
        if x1 == x2:  # Vertical line
            return abs(x - x1) <= tolerance and min(y1, y2) <= y <= max(y1, y2)
        elif y1 == y2:  # Horizontal line
            return abs(y - y1) <= tolerance and min(x1, x2) <= x <= max(x1, x2)
        else:
            # Line equation: (y - y1) = m * (x - x1)
            m = (y2 - y1) / (x2 - x1)
            return abs(y - y1 - m * (x - x1)) <= tolerance

    def display_hsv_on_click(self, event, x, y, flags, param):
        """
        Callback function to display HSV values and set lines on mouse click.
        @param event: The mouse event.
        @param x: X-coordinate of the click.
        @param y: Y-coordinate of the click.
        @param flags: Any relevant flags passed by OpenCV.
        @param param: Additional parameters (frame).
        """
        global mouse_coordinates
        if event == cv2.EVENT_RBUTTONDOWN:
            if len(self.lines) > 0 and len(self.lines[-1]) < 4:
                self.lines[-1].extend([x, y])  # Complete the line
            else:
                self.lines.append([x, y])  # Start a new line
            print(f"Line defined: {self.lines[-1]}")
        if event == cv2.EVENT_LBUTTONDOWN:
            mouse_coordinates = [x, y]

    def load_hsv_values(self):
        """
        Load HSV values from a JSON file if available.
        """
        try:
            with open("player_cv_parameters.json", "r") as file:
                hsv_values = json.load(file)
                self.lower_blue = np.array(hsv_values["lower_blue"], dtype=np.uint8)
                self.upper_blue = np.array(hsv_values["upper_blue"], dtype=np.uint8)
                print("Loaded HSV values from hsv_values.json")
        except FileNotFoundError:
            print("No HSV values file found. Using default values.")

    def run(self):
        """
        Runs the live video feed with detection.
        """
        cv2.namedWindow("Original", cv2.WINDOW_NORMAL)
        cv2.namedWindow("Processed", cv2.WINDOW_NORMAL)
        cv2.namedWindow("Mask", cv2.WINDOW_NORMAL)

        # Enable aspect-ratio scaling for fullscreen
        cv2.setWindowProperty("Original", cv2.WND_PROP_ASPECT_RATIO, cv2.WINDOW_KEEPRATIO)
        cv2.setWindowProperty("Processed", cv2.WND_PROP_ASPECT_RATIO, cv2.WINDOW_KEEPRATIO)
        cv2.setWindowProperty("Mask", cv2.WND_PROP_ASPECT_RATIO, cv2.WINDOW_KEEPRATIO)

        # Create a trackbar for adjusting the ball radius
        def set_radius(val):
            self.group_threshold = max(self.min_area, val)  # Ensure radius is at least min_ball_radius

        def set_min_radius(val):
            self.min_area = max(1, val)  # Ensure minimum radius is at least 1

        cv2.createTrackbar("Ball Radius", "Processed", self.group_threshold, 100, set_radius)
        cv2.createTrackbar("Min Radius", "Processed", self.min_area, 50, set_min_radius)

        # Create trackbars for adjusting HSV values
        def update_lower_h(val):
            self.lower_blue[0] = val

        def update_upper_h(val):
            self.upper_blue[0] = val

        def update_lower_s(val):
            self.lower_blue[1] = val

        def update_upper_s(val):
            self.upper_blue[1] = val

        def update_lower_v(val):
            self.lower_blue[2] = val

        def update_upper_v(val):
            self.upper_blue[2] = val

        cv2.createTrackbar("Lower H", "Processed", self.lower_blue[0], 179, update_lower_h)
        cv2.createTrackbar("Upper H", "Processed", self.upper_blue[0], 179, update_upper_h)
        cv2.createTrackbar("Lower S", "Processed", self.lower_blue[1], 255, update_lower_s)
        cv2.createTrackbar("Upper S", "Processed", self.upper_blue[1], 255, update_upper_s)
        cv2.createTrackbar("Lower V", "Processed", self.lower_blue[2], 255, update_lower_v)
        cv2.createTrackbar("Upper V", "Processed", self.upper_blue[2], 255, update_upper_v)

        while True:
            ret, frame = self.cap.read()
            self.ball_handler.run_frame(frame.copy())
            if not ret:
                print("Failed to capture frame. Exiting.")
                break

            # Set mouse callback for line definition
            cv2.setMouseCallback("Original", self.display_hsv_on_click, frame)

            # Detect shapes intersecting lines
            coords = self.find_shapes_on_lines(frame)

            # Display frames
            cv2.imshow("Original", frame)
            # Highlight the detected area in the processed frame

            key = cv2.waitKey(1) & 0xFF
            if key == ord("q"):  # Quit
                break

        self.cap.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    detector = PlayersDetector(camera_index=1, initial_group_threshold=20)
    detector.run()
