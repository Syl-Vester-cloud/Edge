import sys
import json
import base64
import cv2
import numpy as np
from insightface.app import FaceAnalysis

IMAGE = "./face/top1.jpeg"
# Initialize InsightFace
print("Starting InsightFace...")
app = FaceAnalysis(
    name="buffalo_l",
    providers=["CPUExecutionProvider"]
)
print("Model loaded")
app.prepare(
    ctx_id=0,
    det_size=(640,640)
)
print("InsightFace ready")

if img is None:
   print("image not found")
   exit()

def create_embedding(base64_image):

    # remove header
    if "," in base64_image:
        base64_image = base64_image.split(",")[1]


    image_bytes = base64.b64decode(
        base64_image
    )


    np_arr = np.frombuffer(
        image_bytes,
        np.uint8
    )

    print("Decoding image...")
    img = cv2.imdecode(
        np_arr,
        cv2.IMREAD_COLOR
    )

    print("Image decoded:", img.shape)


    print("Detecting faces...")

    faces = app.get(img)

    print("Faces detected:", len(faces))
    if len(faces) == 0:

        return {
            "success": False,
            "message": "No face detected"
        }


    if len(faces) > 1:

        return {
            "success": False,
            "message": "Multiple faces detected"
        }


    embedding = faces[0].embedding


    return {

        "success": True,

        "embedding": embedding.tolist()

    }



if __name__ == "__main__":


    input_data = sys.stdin.read()


    data = json.loads(
        input_data
    )


    result = create_embedding(
        data["image"]
    )


    print(
        json.dumps(result)
    )