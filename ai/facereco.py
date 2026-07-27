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

ws.settimeout(0.01)
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

           "type": "embedding_not_created",

           "success": False,

           "message": "No face detected"

              }))

        else:

             ws.send(json.dumps({

             "type": "creating_embbeding",

              "success": True,

              "first_name": data["first_name"],

              "last_name": data["last_name"],

              "person_type": data["person_type"],

             "embedding": embedding

              }))

#After we create the embedding then we send it to node and install in the db...

        print("📤 Embedding created and  sent to Node")
    except Exception as e:

        print(
            "Embedding error:",
            e
        )

        return None

 #comapering facess.
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
# FACE PROCESSING AND CREATING EMBEDDING FOR THE LIVE CAMERA..
# ==========================
frame_counter = 0

def process_frame(frame):
    global frame_counter

    frame_counter += 1

    if frame_counter % 30 == 0:
        filename = f"debug_frame_{frame_counter}.jpg"
        cv2.imwrite(filename, frame)
        print("Saved:", filename)
    results = []


    faces = face_engine.get(
        frame
    )
    print("Faces detected:", len(faces))
    
    print(
    "Faces:",
    len(faces),
    [
        round(float(face.det_score), 3)
        for face in faces
    ]
    )
    #called to compare faces from live frames..
    #compare_faces(faces)

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


        print(result,"results")
        results.append(
            result
        )



    return results

def receive_websocket_message():
    print("receiving websocket messages..")

    try:

        message = ws.recv()

        if message:

            data = json.loads(message)

            if data["type"] == "create_embedding":

                print(
                    "Creating embedding..."
                )

                embedding = create_embedding(
                    data["image"],
                    data["first_name"],
                    data["last_name"],
                    data["person_type"]
                )

                response = {
                    "type": "embedding_created",
                    "first_name": data["first_name"],
                    "last_name": data["last_name"],
                    "person_type": data["person_type"],
                    "business": data["business"],
                    "embedding": embedding
                }

                ws.send(
                    json.dumps(response)
                )


    except websocket.WebSocketTimeoutException:

        # no message received
        pass
    

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

    last_log = time.time()

    while True:


        try:

            if time.time() - last_log >= 1:

                print("Reading frames...")

                last_log = time.time()
            buffer += stream.read(4096)



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

            print(
               "JPEG size:",
                len(jpg_bytes)
                 )

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

            print("Frame shape:", frame.shape)

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

            receive_websocket_message()

            time.sleep(
                0.2
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