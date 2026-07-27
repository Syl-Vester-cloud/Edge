const express = require("express");
const axios = require("axios");
const { Pool } = require('pg');
const cors=require("cors");
const fs = require("fs");
const webSocket=require("ws")
const http=require("http");
const { compose } = require("stream");
const app = express();
const server=http.createServer(app)
let pythonSocket = null;
//const YOLO = "/home/mypie/cctv-ai-models/detect.py";
const ESP32_URL = "http://192.168.1.71/stream";
let latestDetection = null;

// store latest frame
let latestFrame = null;
//Databse configuration
   
app.use(express.json({
   limit:"10mb"
}));
app.use(cors({
  origin: function (origin, callback) {
    // Allows your local React server, your Pi IP, or local requests through
    callback(null, true); 
  },
  credentials: true
}));
// 2. PostgreSQL Live Client Infrastructure Pool
const pool = new Pool({
  user: 'postgres',
  host: 'localhost',
  database: 'db',
  password: '1234567', // Replace with the password you wrote in psql earlier
  port: 5432,
  max: 20
});

// 3. Test verification loop confirming database readiness on startup
pool.query('SELECT NOW()', (err, res) => {
  if (err) console.error('❌ Database connection failure:', err.stack);
  else console.log('🚀 PostgreSQL network pipeline live at:', res.rows[0].now);
});
app.post("/signup", async (req, res) => {
console.log("request from UI");
  const { name, ocrEnabled, durationTracking, sharedUsername, sharedPassword } = req.body;
     console.log(req.body,"data from Ui");
  try {
    // Save plain text password directly to the password_hash column
    const queryText = `
      INSERT INTO businesses (name, ocr_enabled, duration_tracking, shared_username, password_hash)
      VALUES ($1, $2, $3, $4, $5)
      RETURNING id, name
    `;
    const values = [name, ocrEnabled, durationTracking, sharedUsername, sharedPassword];
    const result = await pool.query(queryText, values);
    
    const newBusiness = result.rows[0];

    console.log(`📦 Database populated! Created: ${newBusiness.name} (UUID: ${newBusiness.id})`);

    // Hand back raw strings to your React frontend state layout
    res.status(201).json({
      businessId: newBusiness.id,
      name: newBusiness.name
    });

  } catch (err) {
    console.error("Database provisioning block:", err.message);
    res.status(500).json({ error: "Cloud database allocation error." });
  }
});
   ///gadding a persons image and creating embeddings..
app.post("/persons", async(req,res)=>{
    console.log(pythonSocket,"python websocket connection...")

    try {

        console.log("====================");
        console.log("New Person");
        console.log("====================");
        console.log(req.body.first_name);
        console.log(req.body.last_name);
        console.log(req.body.person_type); 
        console.log(req.body.business)
        ////
      let   fn=req.body.first_name
      let     ln=req.body.last_name
      let      pt=req.body.person_type
      let img= req.body.image
      let business=req.body.business

        console.log(
            "Image received:",
            req.body.image.length
        );


        /*
          NEXT:
          Send image to Python
          Generate embedding
        */
       
       if(!pythonSocket){

            return res.status(500).json({

                success:false,

                message:"Python AI not connected"

            });

        }
        console.log("now trying to send it to python...")
       pythonSocket.send(

            JSON.stringify({

                type:"create_embedding",

                first_name:fn,

                last_name:ln,

                person_type:pt,
                business:business,

                image:img

            })
        );

       console.log("image sent to python...")
        res.json({
            success:true,
            message:"Person received"
        });


    } catch(err){

        console.log(err);

        res.status(500).json({
            success:false
        });

    }

});
//sending video to react
app.get("/stream", (req, res) => {
      
    res.writeHead(200, {
        "Content-Type": "multipart/x-mixed-replace; boundary=frame",
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "Pragma": "no-cache"
    });

    const interval = setInterval(() => {

        if (!latestFrame) {
            return;
        }

        res.write("--frame\r\n");
        res.write("Content-Type: image/jpeg\r\n");
        res.write(
            `Content-Length: ${latestFrame.length}\r\n\r\n`
        );

        res.write(latestFrame);
        res.write("\r\n");

    }, 100);   // ~30 FPS

    req.on("close", () => {

        clearInterval(interval);

    });

});
// 2. SIMPLE LOGIN ENDPOINT: Matches raw text strings directly
app.post("/login", async (req, res) => {
console.log("login request")
  const { username, password } = req.body;
  console.log("username", username ,"password" ,password);

  try {
const result = await pool.query(
      "SELECT id,faceid, name, ocr_enabled AS \"ocrEnabled\", duration_tracking AS \"durationTracking\", password_hash FROM businesses WHERE shared_username = $1", 
      [username]
    );
    if (result.rows.length === 0 || result.rows[0].password_hash !== password) {
      return res.status(400).json({ error: "Invalid username or passkey." });
    }

    const business = result.rows[0];
     console.log(business,"business")
    res.json({
      businessId: business.id,
      faceid:business.faceid,
      businessName: business.name,
      ocrEnabled: !!business.ocrEnabled,
      durationTracking: !!business.durationTracking
    });
  } catch (err) {    res.status(500).json({ error: "Internal server error." });
 }
});
// pull frames continuously from ESP32
//discontinued...
//web socket connections

async function startESP32Stream(){
   console.log("Connecting to ESP32 stream...");

    const response = await axios({
        method: "get",
        url: ESP32_URL,
        responseType: "stream"
    });
     console.log("Connected to ESP32 stream...");
    let buffer = Buffer.alloc(0);
    response.data.on(
        "data",
        chunk => {

            buffer = Buffer.concat([
                buffer,
                chunk
            ]);

            const start = buffer.indexOf(
                Buffer.from([0xff,0xd8])
            );

           const end = buffer.indexOf(
          Buffer.from([0xff,0xd9]),
            start + 2
             );

            if(start !== -1 && end !== -1){

                latestFrame = buffer.slice(
                    start,
                    end + 2
                );

                buffer = buffer.slice(   end + 2  );
//console.log( "📸 Frame received:",  "size:", latestFrame.length,"bytes");
            }
            

        }
       
    );

}




const ws = new webSocket.Server({
    server
});

/// cosine function math to comapre faces..
function cosineSimilarity(a, b) {

    let dot = 0;
    let normA = 0;
    let normB = 0;

    for (let i = 0; i < a.length; i++) {

        dot += a[i] * b[i];

        normA += a[i] * a[i];

        normB += b[i] * b[i];
    }

    return dot / (Math.sqrt(normA) * Math.sqrt(normB));
}

function broadcast(data) {

    ws.clients.forEach(client => {

        if (client.readyState === WebSocket.OPEN) {
            client.send(JSON.stringify(data));
        }

    });

}

ws.on("connection", (socket) => {
    console.log("🐍 Python connected");
    pythonSocket = socket;
    socket.on("message",async (message) => {
      latestDetection=message
        console.log("📹 Received", message, "bytes");
         const detection = JSON.parse(message.toString());
         console.log('AI',detection);
         if(detection.type==="creating_embbeding"){
          try {
    // Save plain text password directly to the password_hash column
    const queryText = `
      INSERT INTO persons (first_name, last_name, person_type, embedding, business_id)
      VALUES ($1, $2, $3, $4, $5)
    `;
     const values = [detection.first_name, detection.last_name,
       detection.person_type, detection.embedding,detection.business];
    const result = await pool.query(queryText, values);
    console.log("person embeding successfully added...",result)
  
  }
    catch(e){
      console.log(e,"error insetting embedding..")
    }
  }
      if(detection.type=="face_embedding"){
       console.log("comapering faces..")
       try {
const result = await pool.query(
      "SELECT id, business_id, first_name, last_name, person_type,embedding FROM persons", 
      
    );
    
    const faces_embedding_in_db = result.rows;
    // console.log(dbembedding.embedding.length,"embedding")
     //console.log(faces_embedding_in_db.business_id,"embedding")
     const LivecameraEmbedding=detection.data[0].embedding;
     //compare people
     let bestMatch = null;
let highestScore = -1;

for (const person of faces_embedding_in_db) {

    const score = cosineSimilarity(
        LivecameraEmbedding,
        person.embedding
    );

    console.log(  person.first_name,score,"score...");

    if (score > highestScore) {

        highestScore = score;
        bestMatch = person;

    }

}
   /* res.json({

      businessId: embedding.id,
      'last_name':embedding.first_name,
      'first_name':embedding.last_name,
      embedding:embedding.embedding
     
    });*/
   
  } catch (err) {   console.log(err,"websocket error..")
       
    }
  }
     /// This one was used for broadcasting yolo
     // SO we will comment it out for now..
     // broadcast(detection);
    });

    
    //cloing the websocket connection..
    socket.on("close", () => {

        console.log(
            "🐍 Python disconnected"
        );


        pythonSocket = null;

    });

});
server.listen(80,'0.0.0.0',()=>{
  startESP32Stream();
console.log("server running on 80 and streaming esp32 video")
})
