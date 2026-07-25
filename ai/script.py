import cv2
import time
import urllib.request
import numpy as np
import websocket
import json

from motion import MotionFilter
from tracker import VehicleTracker
from ocr import PlateReader
from detect import ObjectDetector


NODE_WS_URL= "ws://192.168.0.102:80"
TEST_MODE = True


#ESP32_STREAM_URL = "http://192.168.1.71/stream"
NODE_SERVER_URL = "http://192.168.0.102:80/stream"

print("connecting to websocket...")

ws = websocket.create_connection(
    NODE_WS_URL
)

print("connection to node established..")


VEHICLE_CLASSES = [
    "car",
    "truck",
    "bus",
    "motorcycle"
]


def send_detection(data):
    """
    Send AI results to Node.js backend
    """

    payload = {
        "data": data
    }

    print("sending detection data:", payload)

    try:
        ws.send(
            json.dumps(payload)
        )

    except Exception as e:
        print("websocket error:", e)



def start_surveillance_cluster():

    print("🚀 Starting surveillance engine...")
    print(f"📹 Connecting to {NODE_SERVER_URL}")


    motion_gatekeeper = MotionFilter()

    object_detector = ObjectDetector()

    tracker_core = VehicleTracker()

    ocr_interpreter = PlateReader()


    processed_vehicle_ids = set()

    stream_buffer = bytes()



    while True:

        try:

            stream = urllib.request.urlopen(
                NODE_SERVER_URL,
                timeout=10
            )


            print(
                "🟢 Wi-Fi Stream connection established successfully."
            )


            while True:

                stream_buffer += stream.read(1)


                start_marker = stream_buffer.find(
                    b'\xff\xd8'
                )
                end_marker = stream_buffer.find(
                    b'\xff\xd9',
                    start_marker + 2
                )
                if start_marker == -1 or end_marker == -1:
                    continue

                jpg_bytes = stream_buffer[
                    start_marker:end_marker + 2
                ]


                stream_buffer = stream_buffer[
                    end_marker + 2:
                ]
                

                frame = cv2.imdecode(
                    np.frombuffer(
                        jpg_bytes,
                        dtype=np.uint8
                    ),
                    cv2.IMREAD_COLOR
                )
                

                if frame is None:
                    print("Image not found")
                    continue

                if not motion_gatekeeper.has_significant_motion(frame):
                    continue

                detected_objects = object_detector.detect(
                    frame
                )

                print(
                    "YOLO RESULTS:",
                    detected_objects
                )

                send_detection(
                    detected_objects
                )

                if not detected_objects:
                    continue

                vehicle_boxes = []

                for obj in detected_objects:

                    if obj["confidence"] < 0.4:
                        continue

                    print(
                        "OBJECT:",
                        obj["label"],
                        "confidence:",
                        obj["confidence"]
                    )

                    if obj["label"] in VEHICLE_CLASSES:

                        vehicle_boxes.append(
                            obj["box"]
                        )

                # ------------------------
                # TRACK VEHICLES
                # ------------------------

                tracked_vehicles = tracker_core.update_vehicle_tracks(
                    vehicle_boxes
                )


                print(
                    tracked_vehicles,
                    "tracked vehicles"
                )


                for vehicle_id, box in tracked_vehicles.items():

                    if vehicle_id in processed_vehicle_ids:
                        continue

                    x, y, w, h = box

                    y_start = max(
                        0,
                        y
                    )

                    y_end = min(
                        frame.shape[0],
                        y + h
                    )


                    x_start = max(
                        0,
                        x
                    )

                    x_end = min(
                        frame.shape[1],
                        x + w
                    )

                    cropped_vehicle = frame[
                        y_start:y_end,
                        x_start:x_end
                    ]

                    if cropped_vehicle.size == 0:
                        continue

                    cv2.imwrite(
                        f"vehicle_{vehicle_id}.jpg",
                        cropped_vehicle
                    )

                    print(
                        "🚗 Vehicle crop:",
                        cropped_vehicle.shape
                    )

                    plate = ocr_interpreter.extract_plate(
                        cropped_vehicle
                    )

                    print(
                        "OCR returned:",
                        plate
                    )

                    if plate:

                        plate = plate.strip('"').strip("'")

                        print("=" * 40)
                        print(
                            f"🚗 Vehicle {vehicle_id}"
                        )

                        print(
                            f"📋 Plate: {plate}"
                        )

                        print("=" * 40)

                        processed_vehicle_ids.add(
                            vehicle_id
                        )
                        send_detection(
                            {
                                "plateNumber": plate,
                                "vehicleId": vehicle_id
                            }
                        )



        except Exception as e:


            print(
                "⚠️ Surveillance error:",
                e
            )


            print(
                "🔄 Reconnecting stream..."
            )


            time.sleep(2)




if __name__ == "__main__":

    start_surveillance_cluster()
