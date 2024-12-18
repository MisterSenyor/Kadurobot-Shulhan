import cv2
import numpy as np

# Circularity filter bounds
circularity_bounds = {"lower": 0.0, "upper": 1.5}

# Variables for marking the plane
points = []
transform_matrix = None


def update_lower_bound(val):
    circularity_bounds["lower"] = val / 100.0


def update_upper_bound(val):
    circularity_bounds["upper"] = val / 100.0


def mouse_callback(event, x, y, flags, param):
    """
    Callback function to record mouse clicks.
    """
    global points
    if event == cv2.EVENT_LBUTTONDOWN and len(points) < 4:
        poinxts.append((x, y))
        print(f"Point {len(points)}: {x}, {y}")
    elif event == cv2.EVENT_RBUTTONDOWN and points:
        popped_point = points.pop()
        print(f"Removed point: {popped_point}")


def ensure_on_screen(frame, text, x, y, font_scale, thickness):
    """Ensure text or point is displayed within screen boundaries."""
    (text_width, text_height), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, font_scale, thickness)
    frame_height, frame_width = frame.shape[:2]

    if x + text_width > frame_width:
        x = frame_width - text_width - 5
    if y - text_height < 0:
        y = text_height + 5

    return x, y


def detect_yellow_ball_real_time():
    global points, transform_matrix

    # Open a connection to the default camera
    cap = cv2.VideoCapture(1, cv2.CAP_DSHOW)  # Use DirectShow to speed up camera initialization
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 800)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 600)

    # Create a window with trackbars for circularity filter
    cv2.namedWindow("Settings")
    cv2.createTrackbar("Lower Circularity", "Settings", int(circularity_bounds["lower"] * 100), 150, update_lower_bound)
    cv2.createTrackbar("Upper Circularity", "Settings", int(circularity_bounds["upper"] * 100), 150, update_upper_bound)

    # Set mouse callback to get points
    cv2.namedWindow("Yellow Ball Detection")
    cv2.setMouseCallback("Yellow Ball Detection", mouse_callback)

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Failed to grab frame")
            break

        # Draw the selected points on the frame
        for i, point in enumerate(points):
            cv2.circle(frame, point, 5, (0, 0, 255), -1)  # Red dot for each point
            text = f"P{i+1}"
            x, y = ensure_on_screen(frame, text, point[0] + 10, point[1] - 10, 0.5, 1)
            cv2.putText(frame, text, (x, y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)

        # If 4 points are selected, calculate the perspective transform matrix
        if len(points) == 4 and transform_matrix is None:
            # Define the plane in the warped image
            warped_plane = np.array([
                [0, 0], [800, 0], [800, 800], [0, 800]
            ], dtype="float32")
            points_array = np.array(points, dtype="float32")
            transform_matrix = cv2.getPerspectiveTransform(points_array, warped_plane)
            print("Perspective transformation matrix calculated.")

        # Convert to HSV color space
        hsv_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

        # Define a wider HSV range for yellow
        lower_yellow = np.array([15, 80, 80])  # Adjusted lower bound
        upper_yellow = np.array([35, 255, 255])  # Adjusted upper bound

        # Create a mask for yellow
        yellow_mask = cv2.inRange(hsv_frame, lower_yellow, upper_yellow)

        # Morphological operations to reduce noise
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        cleaned_mask = cv2.morphologyEx(yellow_mask, cv2.MORPH_CLOSE, kernel)

        # Find contours
        contours, _ = cv2.findContours(cleaned_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        best_fit = None
        best_score = -1  # Start with an invalid score
        ball_position = None

        for contour in contours:
            # Calculate contour area and perimeter
            area = cv2.contourArea(contour)
            perimeter = cv2.arcLength(contour, True)
            circularity = 4 * np.pi * (area / (perimeter ** 2)) if perimeter > 0 else 0

            # Filter by circularity and area
            if 500 < area < 5000 and circularity_bounds["lower"] <= circularity <= circularity_bounds["upper"]:
                # Calculate yellowness (mean pixel value in the yellow mask)
                mask = np.zeros_like(cleaned_mask)
                cv2.drawContours(mask, [contour], -1, 255, thickness=cv2.FILLED)
                yellowness = cv2.mean(cleaned_mask, mask=mask)[0]

                # Combine circularity and yellowness for scoring
                score = circularity * yellowness

                # Update the best fit based on the score
                if score > best_score:
                    best_fit = contour
                    best_score = score

        if best_fit is not None:
            # Get the bounding box for the best fit
            x, y, w, h = cv2.boundingRect(best_fit)
            ball_center = (x + w // 2, y + h // 2)

            # If the transform matrix is available, map the ball's position
            if transform_matrix is not None:
                ball_position = cv2.perspectiveTransform(
                    np.array([[ball_center]], dtype="float32"), transform_matrix
                )[0][0]

            # Draw the green bounding box around the best fit
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

            # Write the score and circularity index
            text_score = f"Score: {best_score:.2f}"
            text_circ = f"Circ: {circularity:.2f}"
            text_pos = f"Pos: ({int(ball_position[0])}, {int(ball_position[1])})" if ball_position is not None else ""

            x_score, y_score = ensure_on_screen(frame, text_score, x, y - 20, 0.5, 1)
            cv2.putText(frame, text_score, (x_score, y_score), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

            x_circ, y_circ = ensure_on_screen(frame, text_circ, x, y - 40, 0.5, 1)
            cv2.putText(frame, text_circ, (x_circ, y_circ), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

            if text_pos:
                x_pos, y_pos = ensure_on_screen(frame, text_pos, x, y - 60, 0.5, 1)
                cv2.putText(frame, text_pos, (x_pos, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

        # Display the frame with detections
        cv2.imshow("Yellow Ball Detection", frame)

        # Display the mask with contours
        contour_display = np.zeros_like(frame)
        cv2.drawContours(contour_display, contours, -1, (255, 255, 255), 1)
        cv2.imshow("Contours", contour_display)

        # Exit loop when 'q' is pressed
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # Release the camera and close all OpenCV windows
    cap.release()
    cv2.destroyAllWindows()

# Run the real-time detection
detect_yellow_ball_real_time()
