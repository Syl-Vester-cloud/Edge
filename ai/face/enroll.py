import cv2
import json
import numpy as np

from insightface.app import FaceAnalysis


IMAGE = "../top.jpg"
NAME = "Sylvester"

DATABASE = "faces.json"


print("Loading InsightFace...")


app = FaceAnalysis(
    name="buffalo_l"
)

app.prepare(
    ctx_id=-1,
    det_size=(640,640)
)


print("Reading image...")


img = cv2.imread(IMAGE)


if img is None:
    print("Image not found")
    exit()


faces = app.get(img)


if len(faces) == 0:
    print("No face detected")
    exit()


# choose largest face

face = max(
    faces,
    key=lambda x: (x.bbox[2]-x.bbox[0]) *
                  (x.bbox[3]-x.bbox[1])
)


embedding = face.embedding


print("Embedding created")
print("Size:", embedding.shape)


try:
    with open(DATABASE, "r") as f:
        database = json.load(f)

except:
    database = {}


database[NAME] = embedding.tolist()


with open(DATABASE, "w") as f:
    json.dump(database, f)


print("----------------------")
print("Registered:", NAME)
print("----------------------")
