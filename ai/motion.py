import cv2

class MotionFilter:
    """Uses light OpenCV frame arithmetic to ignore static camera feeds."""
    def __init__(self, threshold=25, min_area=3500):
        self.threshold = threshold
        self.min_area = min_area
        self.previous_frame = None

    def has_significant_motion(self, current_frame):
        # Convert frame matrix to low-overhead grayscale and blur noise
        gray = cv2.cvtColor(current_frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (21, 21), 0)

        if self.previous_frame is None:
            self.previous_frame = gray
            return False

        # Compute direct absolute difference between consecutive frames in RAM
        frame_delta = cv2.absdiff(self.previous_frame, gray)
        thresh = cv2.threshold(frame_delta, self.threshold, 255, cv2.THRESH_BINARY)[1]
        thresh = cv2.dilate(thresh, None, iterations=2)

        # Trace contours of moving targets
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        self.previous_frame = gray

        for contour in contours:
            if cv2.contourArea(contour) > self.min_area:
                return True # Significant movement detected! Alert orchestrator
        return False
