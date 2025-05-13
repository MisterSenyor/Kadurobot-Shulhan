import cv2

video_path = "tracking_recording_1747147433.avi"  # Change to your path
cap = cv2.VideoCapture(video_path)

if not cap.isOpened():
    print("❌ Could not open video.")
    exit()

total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
cv2.namedWindow("Frame", cv2.WINDOW_NORMAL)

frame_idx = 0

def show_frame(index):
    cap.set(cv2.CAP_PROP_POS_FRAMES, index)
    ret, frame = cap.read()
    if not ret:
        print(f"⚠️ Failed to read frame {index}")
        return False
    cv2.imshow("Frame", frame)
    print(f"📷 Frame #{index}")
    return True

print("▶️ SPACE = next | ← = previous | q = quit")

while True:
    key = cv2.waitKey(0) & 0xFF

    if key == ord('q'):
        print("👋 Exiting.")
        break
    elif key == 32:  # Spacebar
        if frame_idx < total_frames - 1:
            frame_idx += 1
            show_frame(frame_idx)
    elif key == 8:  # Backspace (←)
        if frame_idx > 0:
            frame_idx -= 1
            show_frame(frame_idx)

cap.release()
cv2.destroyAllWindows()
