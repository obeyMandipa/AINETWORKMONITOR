# 1. Train models
python train.py

# 2. Start ML service
uvicorn app:app --reload --port 8000
// works only in venv conda 

# 3.  Backend
cd Backend
npm run start



# Response:
# {"is_anomaly": true, "anomaly_score": 0.92}

Step 1: Start ML Service (MUST be running first)
bash
cd "ML-services"           # Your ML folder
uvicorn app:app --reload --port 8000
Terminal 1 Output: INFO: Uvicorn running on http://0.0.0.0:8000

Step 2: Start Backend (Terminal 2)
bash
cd Backend
npm run dev
Terminal 2 Output:

text
✅ MongoDB connected
✅ SNMP Collector started - polling every 30 seconds
🚀 Server running on http://localhost:3001

# Step 3: Test Anomaly Detection

iwr -Uri "http://localhost:3001/api/anomaly" -Method POST -Body '{"device_id":"router1","bytes_in":1250000,"bytes_out":987654,"packets_in":5432,"packets_dropped":12,"cpu_usage":25,"latency_ms":28.5}' -ContentType "application/json" | ConvertFrom-Json
