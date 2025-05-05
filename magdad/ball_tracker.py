import time
from collections import deque
import numpy as np

class BallTracker:
    def __init__(self, max_history=5):
        self.positions = [] # Store (x, y, t)

    def update_position(self, x, y):
        now = time.time()
        if x is None or y is None:
            return
        self.positions.append((x, y, now))

    def get_velocity(self):
        if len(self.positions) < 2:
            return None, None

        (x1, y1, t1), (x2, y2, t2) = self.positions[0], self.positions[-1]
        dt = t2 - t1
        if dt == 0:
            return 0.0, 0.0

        vx = (x2 - x1) / dt
        vy = (y2 - y1) / dt
        return vx, vy

    def predict_x_at_y(self, target_y):
        """
        Predicts x when the ball reaches the given y (e.g., your player's row).
        """
        if len(self.positions) < 2:
            return None

        (x1, y1, t1), (x2, y2, t2) = self.positions[-2], self.positions[-1]
        if y2 == y1:
            return None  # Cannot predict if no vertical movement

        vx, vy = self.get_velocity()
        if vy == 0:
            return None  # Would never reach the row

        # Predict time to reach the target y
        time_to_target = (target_y - y2) / vy
        predicted_x = x2 + vx * time_to_target
        return predicted_x

    def get_last_line(self):
        if len(self.positions) < 2:
            return None  # Not enough points for a line

        # Always use only the last 2 positions
        print(self.positions[-2:])
        (x1, y1, _), (x2, y2, _) = self.positions[-2:]

        if x2 == x1:
            return None  # Avoid division by zero

        slope = (y2 - y1) / (x2 - x1)
        intercept = y1 - slope * x1
        return slope, intercept