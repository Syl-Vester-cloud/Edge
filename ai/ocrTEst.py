import cv2
from ultralytics import YOLO

model = YOLO("yolo11n.pt")

from ocr import PlateReader

#TEST_IMAGE = "vehicle_26.jpg"
TEST_IMAGE="imx.jpg"


def start_ocr_test():

    print("🚀 Starting OCR test...")

    # Initialize OCR
    ocr_interpreter = PlateReader()

    # Load image
    frame = cv2.imread(TEST_IMAGE)

    if frame is None:
        print(f"❌ Could not load image: {TEST_IMAGE}")
        return

    print("✅ Image loaded successfully.")
    print("Image size:", frame.shape)

    # Optional: save a copy to confirm you're reading the correct file
    cv2.imwrite("loaded_image.jpg", frame)

    # Show image
   

    # Run OCR
    plate = ocr_interpreter.extract_plate(frame)

    print("\n==============================")

    if plate:
        plate = plate.strip('"').strip("'")
        print("📋 Plate Detected:", plate)
    else:
        print("❌ No plate detected.")

    print("==============================")

    


if __name__ == "__main__":
    start_ocr_test()