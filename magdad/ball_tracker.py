import time
from collections import deque
import numpy as np

MIN_MOVEMENT = 7

class BallTracker:
    def __init__(self, max_history=5):
        self.positions = [] # Store (x, y, t)
        self.max_history = max_history
        self.resting = True
        self.gone = False

    def update_position(self, coordinates: tuple):
        if coordinates is None:
            self.gone = True
            return
        x, y = coordinates
        if x is None or y is None:
            self.gone = True
            return
        
        if self.resting:
            self.resting = False
        if self.gone:
            self.gone = False
        # check if the ball has moved significantly
        if self.positions:
            last_x, last_y, last_t = self.positions[-1]
            dx = x - last_x
            dy = y - last_y
            distance = np.sqrt(dx**2 + dy**2)
            if distance < MIN_MOVEMENT:
                self.resting = True
                return
        if len(self.positions) >= self.max_history:
            self.positions.pop(0)
        self.positions.append((x, y, time.time()))

    def get_position(self):
        if len(self.positions) == 0:
            return None
        return self.positions[-1][:2]

    def get_velocity(self):
        if len(self.positions) < 2:
            return None, None

        vx_list = []
        vy_list = []

        for i in range(1, len(self.positions)):
            x1, y1, t1 = self.positions[i - 1]
            x2, y2, t2 = self.positions[-1]
            vx_list.append((x2 - x1))
            vy_list.append((y2 - y1))

        if not vx_list or not vy_list:
            return None, None

        vx_avg = sum(vx_list) / len(vx_list)
        vy_avg = sum(vy_list) / len(vy_list)
        return vx_avg, vy_avg

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
            return None

        dx, dy = self.get_velocity()
        norm = np.hypot(dx, dy)

        if norm < 1e-6:
            return None  # Movement too small to determine direction

        unit_dx = dx / norm
        unit_dy = dy / norm

        start = self.positions[-1]
        end = (start[0] + unit_dx * 1000, start[1] + unit_dy * 1000)  # 600 pixels forward

        return (int(start[0]), int(start[1])), (int(end[0]), int(end[1]))