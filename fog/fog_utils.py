import time
import numpy as np
import cv2

def reset_fog(self):
        """Resets the fog of the map"""
        if self.fog_mask is not None:
            self.push_undo()
            self.fog_mask = np.zeros_like(self.fog_mask)
            self.update_queue.put("update_all")

def clear_fog(self):
        """Clears all of the fog"""
        if self.fog_mask is not None:
            self.push_undo()
            self.fog_mask = np.ones_like(self.fog_mask) * 255
            self.update_queue.put("update_all")

def reveal_area(self, x, y, force_update=False):
        """Removes the fog where clicked"""
        if self.fog_mask is not None:
            self.push_undo()
            mask = np.zeros_like(self.fog_mask)
            half_size = self.reveal_radius // 2

            x1 = max(0, int(x - half_size))
            y1 = max(0, int(y - half_size))
            x2 = min(self.fog_mask.shape[1], int(x + half_size))
            y2 = min(self.fog_mask.shape[0], int(y + half_size))

            cv2.rectangle(mask, (x1, y1), (x2, y2), 255, -1)

            self.fog_mask = cv2.bitwise_or(self.fog_mask, mask)

            if force_update:
                self.update_queue.put("update_all")
            else:
                current_time = time.time()
                if current_time - self.last_update_time >= self.update_interval:
                    self.update_queue.put("update_all")
                    self.last_update_time = current_time
                elif current_time - self.last_update_time >= 0.01:
                    self.update_queue.put("update_all")
                    self.last_update_time = current_time
