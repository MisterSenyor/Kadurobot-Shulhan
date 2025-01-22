import cv2
import numpy as np
import json
from settings import *

class YellowBallDetector:
    """
    Class for detecting a yellow ball in a live video feed.
    """

    def __init__(self, camera_index=1, initial_ball_radius=20):
        """
        Initialize the YellowBallDetector.
        @param camera_index: Index of the camera (default is 0 for the primary camera).
        @param initial_ball_radius: Initial radius of the ball in pixels.
        """
        self.camera_index = camera_index
        self.ball_radius = initial_ball_radius
        self.min_ball_radius = 5
        self.cap = cv2.VideoCapture(camera_index, cv2.CAP_DSHOW)  # Use CAP_DSHOW for faster loading on Windows

        # HSV range for yellow color based on the uploaded image
        self.lower_yellow = np.array([43, 150, 255])  # Converted to OpenCV HSV range
        self.upper_yellow = np.array([54, 245, 255])  # Converted to OpenCV HSV range

        # Load preset values if available
        self.load_hsv_values()

        # List to store selected points for the quadrilateral
        self.selected_points = []
        self.quad_mask = None
        self.transform_matrix = None

    def find_ball_location(self, frame):
        """
        Finds the location of the yellow ball in the given frame.
        @param frame: The video frame.
        @return: Tuple of (x, y) coordinates of the ball center, or None if not found.
        """
        if self.quad_mask is not None:
            frame = cv2.bitwise_and(frame, frame, mask=self.quad_mask)

        # Convert frame to HSV color space
        hsv_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

        # Threshold the HSV image to get only yellow
        mask = cv2.inRange(hsv_frame, self.lower_yellow, self.upper_yellow)

        # Perform morphological operations to remove noise
        kernel = np.ones((5, 5), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)

        # Find contours in the mask
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        for contour in contours:
            # Calculate area and filter by ball radius
            ((x, y), radius) = cv2.minEnclosingCircle(contour)
            if radius > self.min_ball_radius and radius < self.ball_radius:
                return int(x), int(y), mask

        return None, None, mask

    def on_click(self, event, x, y, flags, param):
        """
        Callback function to display HSV values of a clicked pixel.
        @param event: The mouse event.
        @param x: X-coordinate of the click.
        @param y: Y-coordinate of the click.
        @param flags: Any relevant flags passed by OpenCV.
        @param param: Additional parameters (unused).
        """
        if event == cv2.EVENT_LBUTTONDOWN:
            frame = param
            hsv_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
            hsv_value = hsv_frame[y, x]
            print(f"HSV Value at ({x}, {y}): {hsv_value}")

        elif event == cv2.EVENT_RBUTTONDOWN and len(self.selected_points) < 4:
            self.selected_points.append((x, y))
            print(f"Point {len(self.selected_points)} selected at ({x}, {y})")

            if len(self.selected_points) == 4:
                self.create_quadrilateral_mask(param)
                self.calculate_perspective_transform()

    def create_quadrilateral_mask(self, frame):
        """
        Creates a mask for the quadrilateral defined by the selected points.
        @param frame: The video frame.
        """
        mask = np.zeros(frame.shape[:2], dtype=np.uint8)
        points = np.array(self.selected_points, dtype=np.int32)
        cv2.fillPoly(mask, [points], 255)

        # Create semi-transparent overlay for the quadrilateral
        overlay = frame.copy()
        cv2.polylines(overlay, [points], isClosed=True, color=(0, 255, 0), thickness=2)
        cv2.addWeighted(overlay, 0.3, frame, 0.7, 0, frame)

        self.quad_mask = mask

    def calculate_perspective_transform(self):
        """
        Calculates the perspective transformation matrix based on the selected points.
        """
        if len(self.selected_points) == 4:
            # Define the points for the perspective transform (the 4 points selected)
            quad_points = np.float32(self.selected_points)

            # Define the destination points for the transformation (this should be a rectangle)
            dst_points = np.float32([[0, 0], [BOARD_WIDTH_MM, 0], [BOARD_WIDTH_MM, BOARD_HEIGHT_MM], [0, BOARD_HEIGHT_MM]])

            # Compute the perspective transform matrix
            self.transform_matrix = cv2.getPerspectiveTransform(quad_points, dst_points)

    def apply_perspective_transform(self, x, y):
        """
        Apply the perspective transform to the ball's (x, y) coordinates.
        @param x: The x-coordinate of the ball.
        @param y: The y-coordinate of the ball.
        @return: Transformed (x, y) coordinates.
        """
        if self.transform_matrix is not None:
            ball_point = np.float32([[x, y]])
            transformed_point = cv2.perspectiveTransform(ball_point[None, :, :], self.transform_matrix)
            return transformed_point[0][0]
        return None, None
    
    def plane_length_to_pixels(self, length):
        """
        Convert a length on the transformed plane to pixel length in the original image.

        @param length: The length on the transformed plane.
        @param perspective_matrix: The 3x3 perspective transform matrix.
        @return: Equivalent length in pixels.
        """
        if self.transform_matrix is None:
            return None
        # Define two points separated by the given length on the transformed plane
        point1 = np.array([[0, 0]], dtype=np.float32)  # Starting point
        point2 = np.array([[length, 0]], dtype=np.float32)  # Point at the given length

        # Convert points to homogeneous coordinates
        points_plane = np.array([point1, point2]).reshape(-1, 1, 2)

        # Apply the reverse perspective transform
        points_image = cv2.perspectiveTransform(points_plane, np.linalg.inv(self.transform_matrix))

        # Extract the pixel coordinates from the transformed points
        pixel_point1 = points_image[0, 0]
        pixel_point2 = points_image[1, 0]

        # Calculate the Euclidean distance between the points in pixels
        pixel_length = np.sqrt((pixel_point2[0] - pixel_point1[0]) ** 2 + (pixel_point2[1] - pixel_point1[1]) ** 2)

        return pixel_length
 

    def save_hsv_values(self):
        """
        Save the current HSV values to a JSON file.
        """
        hsv_values = {
            "lower_yellow": self.lower_yellow.tolist(),
            "upper_yellow": self.upper_yellow.tolist()
        }
        with open("hsv_values.json", "w") as file:
            json.dump(hsv_values, file)
        print("HSV values saved to hsv_values.json")

    def load_hsv_values(self):
        """
        Load HSV values from a JSON file if available.
        """
        try:
            # TODO: make this work as a relative path
            with open("C:\\Users\\TLP-001\\Desktop\\Code\\Kadurobot-Shulhan\\magdad\\hsv_values.json", "r") as file:
                hsv_values = json.load(file)
                self.lower_yellow = np.array(hsv_values["lower_yellow"], dtype=np.uint8)
                self.upper_yellow = np.array(hsv_values["upper_yellow"], dtype=np.uint8)
                print("Loaded HSV values from hsv_values.json")
        except FileNotFoundError:
            print("No HSV values file found. Using default values.")

    def get_frame(self):
        _, frame = self.cap.read()
        return frame

    def create_windows(self):
        cv2.namedWindow("Ball-Original", cv2.WINDOW_NORMAL)
        cv2.namedWindow("Ball-Processed", cv2.WINDOW_NORMAL)
        cv2.namedWindow("Ball-Mask", cv2.WINDOW_NORMAL)

        # Enable aspect-ratio scaling for fullscreen
        cv2.setWindowProperty("Ball-Original", cv2.WND_PROP_ASPECT_RATIO, cv2.WINDOW_KEEPRATIO)
        cv2.setWindowProperty("Ball-Processed", cv2.WND_PROP_ASPECT_RATIO, cv2.WINDOW_KEEPRATIO)
        cv2.setWindowProperty("Ball-Mask", cv2.WND_PROP_ASPECT_RATIO, cv2.WINDOW_KEEPRATIO)

        # Create a trackbar for adjusting the ball radius
        def set_radius(val):
            self.ball_radius = max(self.min_ball_radius, val)  # Ensure radius is at least min_ball_radius

        def set_min_radius(val):
            self.min_ball_radius = max(1, val)  # Ensure minimum radius is at least 1

        cv2.createTrackbar("Ball Radius", "Ball-Processed", self.ball_radius, 100, set_radius)
        cv2.createTrackbar("Min Radius", "Ball-Processed", self.min_ball_radius, 50, set_min_radius)

        # Create trackbars for adjusting HSV values
        def update_lower_h(val):
            self.lower_yellow[0] = val

        def update_upper_h(val):
            self.upper_yellow[0] = val

        def update_lower_s(val):
            self.lower_yellow[1] = val

        def update_upper_s(val):
            self.upper_yellow[1] = val

        def update_lower_v(val):
            self.lower_yellow[2] = val

        def update_upper_v(val):
            self.upper_yellow[2] = val

        cv2.createTrackbar("Lower H", "Ball-Processed", self.lower_yellow[0], 179, update_lower_h)
        cv2.createTrackbar("Upper H", "Ball-Processed", self.upper_yellow[0], 179, update_upper_h)
        cv2.createTrackbar("Lower S", "Ball-Processed", self.lower_yellow[1], 255, update_lower_s)
        cv2.createTrackbar("Upper S", "Ball-Processed", self.upper_yellow[1], 255, update_upper_s)
        cv2.createTrackbar("Lower V", "Ball-Processed", self.lower_yellow[2], 255, update_lower_v)
        cv2.createTrackbar("Upper V", "Ball-Processed", self.upper_yellow[2], 255, update_upper_v)

    def run_frame(self, frame):
        """
        Runs the live video feed with ball detection.
        """
        # Set mouse callback to display HSV values on click
        cv2.setMouseCallback("Ball-Original", self.on_click, frame)

        # Get ball location
        ball_x, ball_y, mask = self.find_ball_location(frame)
        transformed_x, transformed_y = None, None

        # Apply perspective transform to ball location
        if ball_x and ball_y:
            transformed_x, transformed_y = self.apply_perspective_transform(ball_x, ball_y)
            cv2.circle(frame, (int(ball_x), int(ball_y)), self.ball_radius, (0, 255, 0), 2)
            if transformed_x is None:
                cv2.putText(frame, f"Ball at ({int(ball_x)}, {int(ball_y)})", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            else:
                cv2.putText(frame, f"TBall at ({int(transformed_x)}, {int(transformed_y)})", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

        # Display selected points
        for point in self.selected_points:
            cv2.circle(frame, point, 5, (255, 0, 0), -1)

        # Display frames
        cv2.imshow("Ball-Original", frame)
        cv2.imshow("Ball-Mask", mask)

        # Highlight the detected area in the processed frame
        processed_frame = cv2.bitwise_and(frame, frame, mask=mask)
        cv2.imshow("Ball-Processed", processed_frame)

        key = cv2.waitKey(1) & 0xFF

        if key == ord("q"):  # Quit if 'q' is pressed
            return None
        elif key == ord("s"):  # Save HSV values if 's' is pressed
            self.save_hsv_values()
        elif key == ord("f"):  # Fullscreen toggle for all windows
            cv2.setWindowProperty("Ball-Original", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
            cv2.setWindowProperty("Ball-Processed", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
            cv2.setWindowProperty("Ball-Mask", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
        
        
        return (transformed_x, transformed_y)

    def exit(self):
        self.cap.release()
        cv2.destroyAllWindows()

    def run(self):
        """
        Runs the live video feed with ball detection.
        """
        self.create_windows()
        while True:
            ret, frame = self.cap.read()
            if not ret:
                print("Failed to capture frame. Exiting.")
                break

            # Set mouse callback to display HSV values on click
            cv2.setMouseCallback("Ball-Original", self.on_click, frame)

            # Get ball location
            ball_x, ball_y, mask = self.find_ball_location(frame)

            # Apply perspective transform to ball location
            if ball_x and ball_y:
                transformed_x, transformed_y = self.apply_perspective_transform(ball_x, ball_y)
                cv2.circle(frame, (int(ball_x), int(ball_y)), self.ball_radius, (0, 255, 0), 2)
                cv2.putText(frame, f"Ball at ({int(transformed_x)}, {int(transformed_y)})", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

            # Display selected points
            for point in self.selected_points:
                cv2.circle(frame, point, 5, (255, 0, 0), -1)

            # Display frames
            cv2.imshow("Ball-Original", frame)
            cv2.imshow("Ball-Mask", mask)

            # Highlight the detected area in the processed frame
            processed_frame = cv2.bitwise_and(frame, frame, mask=mask)
            cv2.imshow("Ball-Processed", processed_frame)

            key = cv2.waitKey(1) & 0xFF

            if key == ord("q"):  # Quit if 'q' is pressed
                break
            elif key == ord("s"):  # Save HSV values if 's' is pressed
                self.save_hsv_values()
            elif key == ord("f"):  # Fullscreen toggle for all windows
                cv2.setWindowProperty("Ball-Original", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
                cv2.setWindowProperty("Ball-Processed", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
                cv2.setWindowProperty("Ball-Mask", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

        # Release resources
        self.cap.release()
        cv2.destroyAllWindows()



if __name__ == "__main__":
    detector = YellowBallDetector(camera_index=0, initial_ball_radius=20)
    detector.run()
