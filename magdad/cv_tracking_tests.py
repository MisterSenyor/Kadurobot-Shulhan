import cv2
from ball_tracker import BallTracker
import ball_cv
import stepper_api

def run_blocking_tracking_from_video(video_path, ball_handler: ball_cv.BallDetector):
    tracker = BallTracker()
    cap = cv2.VideoCapture(video_path)

    if not cap.isOpened():
        print(f"❌ Failed to open video: {video_path}")
        return

    PLAYER_ROW_START = (190, 629)
    PLAYER_ROW_END = (231, 1)

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


if __name__ == "__main__":
    video_path = "../data/test1.mp4"
    ball_handler = ball_cv.BallDetector()
    ball_handler.create_windows()
    run_blocking_tracking_from_video(video_path, ball_handler)
