import cv2
from insightface.app import FaceAnalysis


IMAGE = "top.jpg"


print("Loading InsightFace...")


app = FaceAnalysis(
    name="buffalo_l"
)


app.prepare(
    ctx_id=-1,
    det_size=(640,640)
)


print("Loading image...")


img = cv2.imread(
    IMAGE
)


if img is None:
    print("Image not found")
    exit()


faces = app.get(
    img
)


print(
    "Faces detected:",
    len(faces)
)


for i, face in enumerate(faces):

    bbox = face.bbox.astype(int)

    width = bbox[2] - bbox[0]
    height = bbox[3] - bbox[1]

    if width < 100 or height < 100:
        continue

    print("----------------")
    print("Face:", i)

    print(
        "Bounding box:",
        face.bbox
    )

    print(
        "Embedding size:",
        face.embedding.shape
    )