import cv2
import json
import numpy as np

from insightface.app import FaceAnalysis


TEST_IMAGE = "musk.jpeg"
DATABASE = "faces.json"


print("Loading InsightFace...")


app = FaceAnalysis(
    name="buffalo_l"
)

app.prepare(
    ctx_id=-1,
    det_size=(640,640)
)


img = cv2.imread(TEST_IMAGE)
print("image size{img.nbytes}")

if img is None:
    print("Image not found")
    exit()


faces = app.get(img)


if len(faces) == 0:
    print("No face detected")
    exit()


face = max(
    faces,
    key=lambda x: (x.bbox[2]-x.bbox[0]) *
                  (x.bbox[3]-x.bbox[1])
)


embedding = face.embedding


with open(DATABASE, "r") as f:
    database = json.load(f)


for name, saved_embedding in database.items():

    saved_embedding = np.array(saved_embedding)

    similarity = np.dot(
        embedding,
        saved_embedding
    ) / (
        np.linalg.norm(embedding) *
        np.linalg.norm(saved_embedding)
    )


    print("----------------")
    print("Person:", name)
    print("Similarity:", similarity)


    if similarity > 0.5:
        print("✅ MATCH:", name)

    else:
        print("❌ UNKNOWN")