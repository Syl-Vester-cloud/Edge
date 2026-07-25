import cv2
import time
import urllib.request
import numpy as np
import websocket
import json
import base64

from insightface.app import FaceAnalysis



# ==========================
# NODE CONNECTION
# ==========================

NODE_STREAM_URL = "http://192.168.1.69:80/stream"

NODE_WS_URL = "ws://192.168.1.69:80"



print("Connecting to Node websocket...")


ws = websocket.create_connection(
    NODE_WS_URL
)


print("✅ WebSocket connected")

# ==========================
# INSIGHTFACE SETUP
# ==========================

print("🚀 Loading InsightFace...")

face_engine = FaceAnalysis(
    name="buffalo_l"
)

face_engine.prepare(
    ctx_id=-1,
    det_size=(640,640)
)

print("✅ InsightFace ready")

""
#CREating embedding function
""
def create_embedding(base64_image,first_name,
    last_name,
    person_type):
    
    try:

        # remove data:image/jpeg;base64,
        if "," in base64_image:

            base64_image = base64_image.split(",", 1)[1]


        image_bytes = base64.b64decode(
            base64_image
        )


        image_array = np.frombuffer(
            image_bytes,
            dtype=np.uint8
        )


        image = cv2.imdecode(
            image_array,
            cv2.IMREAD_COLOR
        )


        if image is None:

            print("❌ Image decode failed")

            return None


        print(
            "Enrollment image:",
            image.shape
        )


        faces = face_engine.get(
            image
        )


        print(
            "Enrollment faces:",
            len(faces)
        )


        if len(faces) != 1:

            return None


        embedding = faces[0].embedding


        print(
            "Embedding created:",
            len(embedding)
        )


        return embedding.tolist()
    
        if embedding is None:

           ws.send(json.dumps({

           "type": "embedding_created",

           "success": False,

           "message": "No face detected"

              }))

        else:

             ws.send(json.dumps({

             "type": "embedding_created",

              "success": True,

              "first_name": data["first_name"],

              "last_name": data["last_name"],

              "person_type": data["person_type"],

             "embedding": embedding

              }))

#After we create the embedding then we send it to node and install in the db...

        print("📤 Embedding sent to Node")
    except Exception as e:

        print(
            "Embedding error:",
            e
        )

        return None
# ==========================
# SEND DATA TO NODE
# ==========================


def send_detection(data):


    payload = {

        "type": "face_embedding",

        "data": data

    }


    try:

        ws.send(
            json.dumps(payload)
        )


        print(
            "📤 Sent face data"
        )


    except Exception as e:


        print(
            "WebSocket error:",
            e
        )



# ==========================
# FACE PROCESSING
# ==========================


def process_frame(frame):


    results = []


    faces = face_engine.get(
        frame
    )
    print("Faces detected:", len(faces))

    for face in faces:

        width = (

            face.bbox[2]
            -
            face.bbox[0]

        )

        height = (

            face.bbox[3]
            -
            face.bbox[1]

        )
        # Ignore tiny false detections

        if width < 80 or height < 80:

            continue

        result = {
         "embedding":
                face.embedding.tolist(),


            "box":
                face.bbox.astype(
                    int
                ).tolist(),


            "det_score":
                float(
                    face.det_score
                )

        }



        results.append(
            result
        )



    return results



# ==========================
# STREAM READER HTTP reading live frames from python..
# ==========================


def start_face_recognition():


    print(
        "📹 Connecting to Node stream..."
    )


    stream = urllib.request.urlopen(

        NODE_STREAM_URL,

        timeout=10

    )


    print(
        "✅ Stream connected"
    )



    buffer = bytes()



    while True:


        try:


            buffer += stream.read(1)



            start_marker = buffer.find(
                b'\xff\xd8'
            )


            end_marker = buffer.find(

                b'\xff\xd9',

                start_marker + 2

            )



            if start_marker == -1 or end_marker == -1:

                continue



            jpg_bytes = buffer[

                start_marker:end_marker+2

            ]



            buffer = buffer[

                end_marker+2:

            ]



            frame = cv2.imdecode(

                np.frombuffer(

                    jpg_bytes,

                    dtype=np.uint8

                ),

                cv2.IMREAD_COLOR

            )



            if frame is None:

                continue



            faces = process_frame(
                frame
            )



            if faces:


                print(
                    "Detected faces:",
                    len(faces)
                )


                send_detection(
                    faces
                )



            time.sleep(
                0.2
            )

            #receiving websocket messages from nodejs
            message = ws.recv()


            data = json.loads(
            message
            )


            if data["type"] == "create_embedding":
               print(type(data["image"]))
               print(len(data["image"]))
               print(data["image"][:50]) 
               print(
               "Creating embedding for:",
               data["first_name"]
               )


               embedding = create_embedding(
                data["image"],
                data["first_name"],
                data["last_name"],
                data["person_type"]
                )


               response = {

                "type":"embedding_created",

                "first_name":data["first_name"],

                "last_name":data["last_name"],

                "person_type":data["person_type"],

                "embedding":embedding

                }


               ws.send(
                json.dumps(response)
                )


               print(
                "📤 Embedding sent to Node"
                )

        except Exception as e:


                  print(
                "⚠️ Stream error:",
                e
               )


    time.sleep(2)




# ==========================
# MAIN
# ==========================


if __name__ == "__main__":


    start_face_recognition()