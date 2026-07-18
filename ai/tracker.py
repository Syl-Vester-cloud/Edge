import numpy as np
from scipy.optimize import linear_sum_assignment
import time

class VehicleTracker:
    """A clean, production-grade spatial tracking engine optimized for Pi CPUs."""
    def __init__(self, max_disappeared=5, min_iou=0.3):
        self.next_vehicle_id = 1
        self.tracked_objects = {}  # Format -> { id: (x, y, w, h) }
        self.disappeared_counter = {}  # Counts how many frames a car was missed before deleting it
        self.max_disappeared = max_disappeared
        self.min_iou = min_iou

    def _calculate_iou(self, boxA, boxB):
        """Computes Intersection-over-Union spatial overlaps between bounding vectors."""
        xA = max(boxA[0], boxB[0])
        yA = max(boxA[1], boxB[1])
        xB = min(boxA[0] + boxA[2], boxB[0] + boxB[2])
        yB = min(boxA[1] + boxA[3], boxB[1] + boxB[3])

        interArea = max(0, xB - xA) * max(0, yB - yA)
        boxAArea = boxA[2] * boxA[3]
        boxBArea = boxB[2] * boxB[3]

        if float(boxAArea + boxBArea - interArea) == 0:
            return 0
            
        return interArea / float(boxAArea + boxBArea - interArea)

    def update_vehicle_tracks(self, current_frame_boxes):
        """Assigns persistent tracking IDs to freshly detected bounding frames."""
        # If no boxes are detected in the current frame, increase the missing counters
        if len(current_frame_boxes) == 0:
            for object_id in list(self.disappeared_counter.keys()):
                self.disappeared_counter[object_id] += 1
                if self.disappeared_counter[object_id] > self.max_disappeared:
                    del self.tracked_objects[object_id]
                    del self.disappeared_counter[object_id]
            return self.tracked_objects

        object_ids = list(self.tracked_objects.keys())
        object_boxes = list(self.tracked_objects.values())

        # If we aren't tracking anything yet, register all new incoming boxes
        if len(self.tracked_objects) == 0:
            for box in current_frame_boxes:
                self._register_object(box)
            return self.tracked_objects

        # Build a cost matrix based on spatial intersection overflows
        cost_matrix = np.zeros((len(object_boxes), len(current_frame_boxes)), dtype=np.float32)
        for i, old_box in enumerate(object_boxes):
            for j, new_box in enumerate(current_frame_boxes):
                cost_matrix[i, j] = 1.0 - self._calculate_iou(old_box, new_box)

        # High-speed Hungarian algorithm solver matches tracks across frame ticks
        row_ind, col_ind = linear_sum_assignment(cost_matrix)

        assigned_rows = set()
        assigned_cols = set()

        for r, c in zip(row_ind, col_ind):
            # If the spatial overlap is too low, don't match them
            if cost_matrix[r, c] > (1.0 - self.min_iou):
                continue

            object_id = object_ids[r]
            self.tracked_objects[object_id] = current_frame_boxes[c]
            self.disappeared_counter[object_id] = 0
            assigned_rows.add(r)
            assigned_cols.add(c)

        # Handle tracks that disappeared from view
        for i in range(len(object_boxes)):
            if i not in assigned_rows:
                object_id = object_ids[i]
                self.disappeared_counter[object_id] += 1
                if self.disappeared_counter[object_id] > self.max_disappeared:
                    del self.tracked_objects[object_id]
                    del self.disappeared_counter[object_id]

        # Register completely new vehicle footprints
        for j in range(len(current_frame_boxes)):
            if j not in assigned_cols:
                self._register_object(current_frame_boxes[j])

        return self.tracked_objects

    def _register_object(self, box):
        self.tracked_objects[self.next_vehicle_id] = box
        self.disappeared_counter[self.next_vehicle_id] = 0
        self.next_vehicle_id += 1
