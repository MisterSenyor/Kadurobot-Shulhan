import time

import cv2
import keyboard

import ball_cv
import settings
import json

def run_ball_tracking_on_video_manual(json_path):
    with open(json_path, 'r') as f:
        json_data = json.load(f)
    video_path = json_data["path"]
    # Create BallDetector without using a live camera
    ball_handler = ball_cv.BallDetector(camera_index=0)  # camera_index ignored, will override .cap

    # Override the VideoCapture to use the video file
    ball_handler.cap = cv2.VideoCapture(video_path)

    if not ball_handler.cap.isOpened():
        print(f"Error opening video file: {video_path}")
        return

    ball_handler.create_windows()  # Create display windows
    ball_handler.selected_points = json_data["table_points"]
    ret, frame = ball_handler.cap.read()
    ball_handler.create_quadrilateral_mask(frame)
    ball_handler.calculate_perspective_transform()

    frame_number = 0
    while True:
        ret, frame = ball_handler.cap.read()
        if not ret:
            print("End of video.")
            break

        # Run ball detection on the current frame

        frame_number += 1
        coordinates = ball_handler.run_frame(frame)
        if coordinates is not None and coordinates[0] is not None and coordinates[1] is not None:
            print(f"Frame {frame_number}: Ball at ({coordinates[0]:.2f}, {coordinates[1]:.2f})")
        else:
            print(f"Frame {frame_number}: No ball detected.")
            
        # --- Wait for user key ---
        print("Press SPACE to go to next frame, or 'q' to quit.")
        while True:
            key = cv2.waitKey(0) & 0xFF
            if key == ord(' '):  # SPACE key
                break
            elif key == ord('r'):
                coordinates = ball_handler.run_frame(frame)
                if coordinates is not None and coordinates[0] is not None and coordinates[1] is not None:
                    print(f"Frame {frame_number}: Ball at ({coordinates[0]:.2f}, {coordinates[1]:.2f})")
                else:
                    print(f"Frame {frame_number}: No ball detected.")
            elif key == ord('q'):
                print("Stopped by user.")
                ball_handler.exit()
                return

    # Release resources at the end
    ball_handler.exit()



if __name__ == "__main__":
    json_path = "../data/test3.json"
    run_ball_tracking_on_video_manual(json_path)
