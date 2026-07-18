import cv2
from ultralytics import YOLO


class ObjectDetector:
    """
    Generic YOLOv8 object detector.
    Returns all detected objects so the surveillance engine can decide
    how to process each one.
    """

    def __init__(self, weights_path="yolov8n.pt"):
        print("⚡ Loading local YOLOv8 neural network weights into memory...")
        self.model = YOLO(weights_path)

    def detect(self, frame):
        """
        Runs YOLO inference on an OpenCV frame.

        Returns:
            [
                {
                    "label": "car",
                    "confidence": 0.92,
                    "box": (x, y, w, h)
                },
                ...
            ]
        """

        results = self.model(
            frame,
            verbose=False,
            device="cpu"
        )

        detected_objects = []

        for box in results[0].boxes:

            class_id = int(box.cls[0])
            confidence = float(box.conf[0])

            label = self.model.names[class_id]

            x1, y1, x2, y2 = map(int, box.xyxy[0])

            detected_objects.append({
                "label": label,
                "confidence": confidence,
                "box": (
                    x1,
                    y1,
                    x2 - x1,
                    y2 - y1
                )
            })

        return detected_objects
