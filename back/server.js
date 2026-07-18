const express = require("express");
const axios = require("axios");
const { Pool } = require('pg');
const cors=require("cors");
const fs = require("fs");
const webSocket=require("ws")
const http=require("http")
const app = express();
const server=http.createServer(app)
//const YOLO = "/home/mypie/cctv-ai-models/detect.py";
const ESP32_URL = "http://192.168.1.71/stream";
let latestDetection = null;
// store latest frame
let latestFrame = null;
//Databse configuration
   
app.use(express.json());
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
   ///getting detections from python
app.post("/api/detection/log", (req, res) => {

    console.log("=================================");
    console.log("📥 Detection received from Python");
    console.log(req.body);
    console.log("=================================");

    res.json({
        success: true
    });

});
//getting live video stream from  python
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
      "SELECT id, name, ocr_enabled AS \"ocrEnabled\", duration_tracking AS \"durationTracking\", password_hash FROM businesses WHERE shared_username = $1", 
      [username]
    );
    if (result.rows.length === 0 || result.rows[0].password_hash !== password) {
      return res.status(400).json({ error: "Invalid username or passkey." });
    }

    const business = result.rows[0];
     console.log(business,"business")
    res.json({
      businessId: business.id,
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
const ESP32_STREAM_URL = "http://192.168.1.71/stream";


async function startESP32Stream(){

    const response = await axios({
        method: "get",
        url: ESP32_STREAM_URL,
        responseType: "stream"
    });


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
                Buffer.from([0xff,0xd9])
            );


            if(start !== -1 && end !== -1){

                latestFrame = buffer.slice(
                    start,
                    end + 2
                );


                buffer = buffer.slice(
                    end + 2
                );

            }

        }
    );

}





const ws = new webSocket.Server({
    server
});

ws.on("connection", (socket) => {
    console.log("🐍 Python connected");

    socket.on("message", (message) => {
      latestFrame=message
        console.log("📹 Received", message, "bytes");
         const detection = JSON.parse(message.toString());
         console.log('AI',detection);
    });
});
server.listen(80,'0.0.0.0',()=>{
  startESP32Stream();
console.log("server running on 80 and streaming esp32 video")
})
