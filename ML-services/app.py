# FastAPI server app.py

"""
Docstring for ML-services.app
AI Network Anomaly Detection FastAPI application.
This module defines a FastAPI application that serves as an API for
network anomaly detection using machine learning models. It includes
endpoints for health checks, anomaly predictions, and retrieving recent
network metrics from a MongoDB database.
"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from Models.isolation_forest import AnomalyDetector
import pymongo
import pandas as pd
import numpy as np
import joblib
from preprocess import NetworkPreprocessor
from datetime import datetime
from typing import Optional

app = FastAPI(title="AI Network Anomaly Detection")

# Initialize preprocessor first
preprocessor = NetworkPreprocessor()
try:
    preprocessor.scaler = joblib.load('Models/nsl_kdd_scaler.pkl')
except Exception as e:
    print(f"Could not load scaler: {e}")

# Load models
detector = AnomalyDetector()
try:
    detector.load()
except Exception as e:
    print(f"Could not load detector model, skipping training: {e}")
    pass

try:
    mongo_client = pymongo.MongoClient("mongodb://localhost:27017/", serverSelectionTimeoutMS=5000)
    db = mongo_client["network_monitor"]
    metrics_collection = db["trafficmetrics"]
except Exception as e:
    print(f"Could not connect to MongoDB: {e}")
    mongo_client = None
    metrics_collection = None

class MetricInput(BaseModel):
    device_id: str
    bytes_in: float
    bytes_out: float
    packets_in: float
    packets_dropped: float
    cpu_usage: float
    latency_ms: float
    timestamp: Optional[str] = None

@app.get("/health")
def health():
    return {"status": "healthy", "model": "loaded"}

@app.post("/predict")
def predict_anomaly(metric: MetricInput):
    try:
        # Direct anomaly detection based on SNMP metrics
        data = metric.dict()
        
        # Simple heuristic-based anomaly detection for SNMP metrics
        # Check for anomalous patterns
        is_anomaly = False
        anomaly_reason = []
        
        # High CPU usage indicates potential anomaly
        if data.get('cpu_usage', 0) > 80:
            is_anomaly = True
            anomaly_reason.append("High CPU usage")
        
        # High packet drop rate indicates potential anomaly
        if data.get('packets_in', 0) > 0:
            drop_rate = data.get('packets_dropped', 0) / data.get('packets_in', 1)
            if drop_rate > 0.05:  # >5% drop rate
                is_anomaly = True
                anomaly_reason.append("High packet drop rate")
        
        # High latency indicates potential anomaly
        if data.get('latency_ms', 0) > 100:
            is_anomaly = True
            anomaly_reason.append("High latency")
        
        # Calculate anomaly score (0-1)
        anomaly_score = 0.0
        if data.get('cpu_usage', 0) > 50:
            anomaly_score += 0.3 * (data.get('cpu_usage', 0) - 50) / 50
        if data.get('packets_in', 0) > 0:
            drop_rate = data.get('packets_dropped', 0) / data.get('packets_in', 1)
            if drop_rate > 0.01:
                anomaly_score += 0.4 * min(drop_rate / 0.1, 1.0)
        if data.get('latency_ms', 0) > 50:
            anomaly_score += 0.3 * min((data.get('latency_ms', 0) - 50) / 100, 1.0)
        
        anomaly_score = min(anomaly_score, 1.0)
        
        return {
            "is_anomaly": is_anomaly,
            "anomaly_score": float(anomaly_score),
            "reason": ", ".join(anomaly_reason) if anomaly_reason else "Normal",
            "device_id": data.get('device_id'),
            "timestamp": data.get('timestamp', datetime.now().isoformat())
        }
    except Exception as e:
        print(f"Prediction error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/recent-metrics/{device_id}")
def get_recent_metrics(device_id: str, limit: int = 100):
    metrics = list(metrics_collection.find({"device_id": device_id}).sort("timestamp", -1).limit(limit))
    return metrics

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
