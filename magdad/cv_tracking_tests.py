import cv2
from ball_tracker import BallTracker
import ball_cv
import stepper_api
import settings
import requests
import numpy as np
import time




THIRD = settings.BOARD_HEIGHT_MM // 3
linear_stepper_handler = stepper_api.StepperHandler(settings.PORT)
IP_CAM_URL = "http://192.168.178.121:8080/shot.jpg"



def run_blocking_tracking_from_video(video_path, ball_handler: ball_cv.BallDetector):
    with open(json_path, 'r') as f:
        json_data = json.load(f)
    video_path = json_data["path"]
    tracker = BallTracker()
    cap = cv2.VideoCapture(video_path)

    if not cap.isOpened():
        print(f"❌ Failed to open video: {video_path}")
        return

    PLAYER_ROW_START = (190, 629)
    PLAYER_ROW_END = (231, 1)

    ball_handler.selected_points = json_data["table_points"]
    ret, frame = cap.read()
    ball_handler.create_quadrilateral_mask(frame)
    ball_handler.calculate_perspective_transform()

    frame_idx = 0

    while True:
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        if key != 32:
            continue

        ret, frame = cap.read()
        if not ret or frame is None:
            print("📼 End of video or cannot read frame.")
            break

        try:
            h, w = frame.shape[:2]
            if h <= 1 or w <= 1:
                print(f"❌ Invalid frame size: {h}x{w}")
                continue
        except Exception as e:
            print(f"❌ Error reading frame shape: {e}")
            continue

        frame_idx += 1
        print(f"🟩 Frame #{frame_idx}")

        # Ball detection
        coordinates = ball_handler.run_frame(frame)
        new_frame = frame
        if new_frame is not None:
            frame = new_frame
        print(f"[DEBUG] After run_frame: frame is None? {frame is None}, shape: {getattr(frame, 'shape', 'no shape')}")

        # Always draw player line
        cv2.line(frame, PLAYER_ROW_START, PLAYER_ROW_END, (0, 255, 0), 2)

        print(coordinates)
        # Try prediction and draw
        if coordinates is not None:
            coordinates = ball_handler.find_ball_location(frame)
            tracker.update_position(coordinates[0], coordinates[1])

            # Get the line representing ball movement
            ball_line = tracker.get_last_line()
            if ball_line is not None:
                print("🟩 Ball line detected.")
                slope, intercept = ball_line
                height, width = frame.shape[:2]

                # Calculate line endpoints across the width of the image
                x1 = 0
                y1 = int(slope * x1 + intercept)

                x2 = width - 1
                y2 = int(slope * x2 + intercept)

                # Draw the predicted motion line
                cv2.line(frame, (x1, y1), (x2, y2), (255, 255, 0), 2)  # Light blue line

            prediction = predict_intersection(tracker, PLAYER_ROW_START, PLAYER_ROW_END)

            if prediction is not None:
                pred_x, pred_y = prediction
                frame_height, frame_width = frame.shape[:2]

                if 0 <= pred_x < frame_width and 0 <= pred_y < frame_height:
                    if is_point_on_segment((pred_x, pred_y), PLAYER_ROW_START, PLAYER_ROW_END):
                        print(f"🔴 Prediction at ({pred_x:.1f}, {pred_y:.1f}) [inside segment]")
                        cv2.circle(frame, (int(pred_x), int(pred_y)), 10, (0, 0, 255), -1)
                         # ✅ Transform the predicted point into the plane
                        transformed_point = ball_handler.apply_perspective_transform(pred_x, pred_y)
                        if transformed_point.any():
                            transformed_x, transformed_y = transformed_point
                            print(f"📐 Transformed prediction: ({transformed_x:.1f}, {transformed_y:.1f})")

                            moving_mms = coordinates[0] % THIRD
                            linear_stepper_handler.move_to_mm(moving_mms)
                    else:
                        print(f"❌ Prediction outside segment: ({pred_x:.1f}, {pred_y:.1f})")
                        closest_point = closest_endpoint((pred_x, pred_y), PLAYER_ROW_START, PLAYER_ROW_END)
                        draw_x(frame, closest_point, size=15, color=(255, 0, 0), thickness=2)
                else:
                    print(f"❌ Prediction out of bounds: ({pred_x:.1f}, {pred_y:.1f})")
            else:
                print("❌ No prediction this frame.")

        # SHOW frame only if valid
        if frame is not None and frame.shape[0] > 1 and frame.shape[1] > 1:
            cv2.imshow("Main", frame)
        else:
            print("⚠️ Frame invalid at display time.")

    cap.release()
    ball_handler.cap.release()
    cv2.destroyAllWindows()


def predict_intersection(tracker, player_start, player_end):
    ball_line = tracker.get_last_line()
    if ball_line is None:
        return None

    ball_slope, ball_intercept = ball_line
    x1, y1 = player_start
    x2, y2 = player_end

    if x1 == x2:
        x = x1
        y = ball_slope * x + ball_intercept
    else:
        player_slope = (y2 - y1) / (x2 - x1)
        player_intercept = y1 - player_slope * x1

        if ball_slope == player_slope:
            return None

        x = (player_intercept - ball_intercept) / (ball_slope - player_slope)
        y = ball_slope * x + ball_intercept

    return (x, y)


def is_point_on_segment(point, start, end, tolerance=1e-6):
    px, py = point
    x1, y1 = start
    x2, y2 = end
    return (min(x1, x2) - tolerance <= px <= max(x1, x2) + tolerance) and \
           (min(y1, y2) - tolerance <= py <= max(y1, y2) + tolerance)


def closest_endpoint(pred_point, start, end):
    px, py = pred_point
    sx, sy = start
    ex, ey = end
    dist_start = (px - sx) ** 2 + (py - sy) ** 2
    dist_end = (px - ex) ** 2 + (py - ey) ** 2
    return start if dist_start < dist_end else end


def draw_x(frame, center, size=10, color=(0, 0, 255), thickness=2):
    x, y = center
    cv2.line(frame, (x - size, y - size), (x + size, y + size), color, thickness)
    cv2.line(frame, (x - size, y + size), (x + size, y - size), color, thickness)










def fetch_ip_frame(url=IP_CAM_URL):
    try:
        response = requests.get(url, timeout=1)
        img_array = np.asarray(bytearray(response.content), dtype=np.uint8)
        frame = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
        return frame
    except Exception as e:
        print(f"❌ Failed to fetch frame: {e}")
        return None

def run_blocking_tracking_from_ipcam_live(json_path, ball_handler: ball_cv.BallDetector):

    tracker = BallTracker()
    with open(json_path, 'r') as f:
        json_data = json.load(f)

    PLAYER_ROW_START = json_data["rows"][0][0]
    PLAYER_ROW_END =  json_data["rows"][0][1]
    recording = False
    video_writer = None
    frame_idx = 0

    ball_handler.selected_points = json_data["table_points"]

    # Wait for first good frame to calibrater
    while True:
        frame = fetch_ip_frame(IP_CAM_URL)
        if frame is not None and frame.shape[0] > 0:
            break
        time.sleep(0.5)

    ball_handler.create_quadrilateral_mask(frame)
    ball_handler.calculate_perspective_transform()

    print("🎮 Press 'r' to record, 's' to stop, 'q' to quit.")

    while True:
        frame = fetch_ip_frame(IP_CAM_URL)
        if frame is None or frame.shape[0] <= 1 or frame.shape[1] <= 1:
            continue

        frame_idx += 1
        key = cv2.waitKey(1) & 0xFF

        if key == ord("q"):
            break
        elif key == ord("r") and not recording:
            recording = True
            h, w = frame.shape[:2]
            fourcc = cv2.VideoWriter_fourcc(*"XVID")
            filename = f"ipcam_recording_{int(time.time())}.avi"
            video_writer = cv2.VideoWriter(filename, fourcc, 20.0, (w, h))
            print(f"⏺️ Started recording to {filename}")
        elif key == ord("s") and recording:
            recording = False
            if video_writer:
                video_writer.release()
                video_writer = None
                print("⏹️ Stopped recording.")

        # Process frame
        coordinates = ball_handler.run_frame(frame)
        cv2.line(frame, PLAYER_ROW_START, PLAYER_ROW_END, (0, 255, 0), 2)

        if coordinates is not None and coordinates[0] is not None and coordinates[1] is not None:
            coordinates = ball_handler.find_ball_location(frame)
            tracker.update_position(coordinates[0], coordinates[1])

            ball_line = tracker.get_last_line()
            if ball_line is not None:
                slope, intercept = ball_line
                h, w = frame.shape[:2]
                x1, y1 = 0, int(slope * 0 + intercept)
                x2, y2 = w - 1, int(slope * (w - 1) + intercept)
                cv2.line(frame, (x1, y1), (x2, y2), (255, 255, 0), 2)

            prediction = predict_intersection(tracker, PLAYER_ROW_START, PLAYER_ROW_END)
            if prediction is not None:
                pred_x, pred_y = prediction
                if 0 <= pred_x < frame.shape[1] and 0 <= pred_y < frame.shape[0]:
                    if is_point_on_segment((pred_x, pred_y), PLAYER_ROW_START, PLAYER_ROW_END):
                        cv2.circle(frame, (int(pred_x), int(pred_y)), 10, (0, 0, 255), -1)
                        transformed_point = ball_handler.apply_perspective_transform(pred_x, pred_y)
                        if transformed_point.any():
                            transformed_x, transformed_y = transformed_point
                            moving_mms = coordinates[0] % THIRD
                            linear_stepper_handler.move_to_mm(moving_mms)
                    else:
                        closest = closest_endpoint((pred_x, pred_y), PLAYER_ROW_START, PLAYER_ROW_END)
                        draw_x(frame, closest, size=15, color=(255, 0, 0), thickness=2)

        # Recording?
        if recording and video_writer:
            video_writer.write(frame)
        label = "Recording..." if recording else "Live"
        cv2.putText(frame, label, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1,
                    (0, 0, 255) if recording else (0, 255, 0), 2)
        cv2.namedWindow("IPCam Tracking", cv2.WINDOW_NORMAL)
        cv2.imshow("IPCam Tracking", frame)

    if video_writer:
        video_writer.release()
    cv2.destroyAllWindows()






def run_calibration_click_test(source_name="Calibration", fetch_frame_func=None):
    """
    Lets the user click on points and prints the coordinates.
    @param source_name: name of the window
    @param fetch_frame_func: a function that returns a frame (for IP cam, webcam, etc.)
    """
    points = []

    def click_callback(event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            print(f"🖱️ Click at: ({x}, {y})")
            points.append((x, y))
            cv2.circle(param, (x, y), 5, (0, 255, 0), -1)

    print("🔧 Click to select points. Press 'q' to quit.")

    while True:
        frame = fetch_frame_func() if fetch_frame_func else None
        if frame is None:
            print("❌ No frame received.")
            break

        display_frame = frame.copy()
        cv2.namedWindow(source_name, cv2.WINDOW_NORMAL)

        cv2.setMouseCallback(source_name, click_callback, display_frame)

        cv2.imshow(source_name, display_frame)
        key = cv2.waitKey(10) & 0xFF
        if key == ord("q"):
            break

    cv2.destroyAllWindows()
    print("✅ Final selected points:")
    for i, (x, y) in enumerate(points):
        print(f"  Point {i + 1}: ({x}, {y})")

    return points

import cv2
import json

def run_calibration_and_save(output_path, fetch_frame_func):
    points = []
    labels = []

    def click_callback(event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            print(f"🖱️ Click at: ({x}, {y})")
            points.append((x, y))
            cv2.circle(param, (x, y), 5, (0, 255, 0), -1)

    print("📐 Select 4 table corners, then 3 row lines (2 points per row).")
    print("Total: 10 points. Press 'q' to cancel early.")

    while True:
        frame = fetch_frame_func()
        if frame is None:
            print("❌ No frame received.")
            break

        display = frame.copy()
        cv2.namedWindow("Calibration", cv2.WINDOW_NORMAL)
        cv2.setMouseCallback("Calibration", click_callback, display)

        for pt in points:
            cv2.circle(display, pt, 5, (0, 255, 0), -1)

        cv2.imshow("Calibration", display)

        key = cv2.waitKey(10) & 0xFF
        if key == ord('q'):
            print("❌ Calibration cancelled.")
            break
        if len(points) >= 10:
            print("✅ All points collected.")
            break

    if len(points) < 10:
        cv2.destroyAllWindows()
        return

    # Split points into table and rows
    table_points = points[:4]
    row_points = points[4:]
    rows = [ [row_points[i], row_points[i+1]] for i in range(0, len(row_points), 2) ]

    data = {
        "table_points": table_points,
        "rows": rows
    }

    with open(output_path, 'w') as f:
        json.dump(data, f, indent=4)

    print(f"✅ Calibration data saved to: {output_path}")
    cv2.destroyAllWindows()




if __name__ == "__main__":
    # json_path = "../data/test3.json"
    json_path = "../data/camera_data.json"
    #run_calibration_and_save(json_path, fetch_frame_func=fetch_ip_frame)
    ball_handler = ball_cv.BallDetector()
    ball_handler.create_windows()
    ball_handler.cap = None
    # run_blocking_tracking_from_video(json_path, ball_handler)
    run_blocking_tracking_from_ipcam_live(json_path, ball_handler)
    # run_calibration_click_test("calibration", fetch_frame_func=fetch_ip_frame)
