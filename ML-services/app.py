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

app = FastAPI(title="AI Network Anomaly Detection")

# Load models
detector = AnomalyDetector()
try:
    detector.load()
except:
    print("Training new model...")
    # Train on NSL-KDD
    X_train, _, _ = preprocessor.prepare_nsl_kdd('data/raw/KDDTrain+.csv', 'data/raw/KDDTest+.csv')
    detector.train(X_train)

preprocessor = NetworkPreprocessor()
try:
    preprocessor.scaler = joblib.load('models/scaler.joblib')
except:
    pass

mongo_client = pymongo.MongoClient("mongodb://host.docker.internal:27017/")
db = mongo_client["network_monitor"]
metrics_collection = db["trafficmetrics"]

class MetricInput(BaseModel):
    device_id: str
    bytes_in: float
    bytes_out: float
    packets_in: float
    packets_dropped: float
    cpu_usage: float
    latency_ms: float

@app.get("/health")
def health():
    return {"status": "healthy", "model": "loaded"}

@app.post("/predict")
def predict_anomaly(metric: MetricInput):
    # Feature engineering
    df = pd.DataFrame([metric.dict()])
    features = preprocessor.snmp_features(df)
    
    # Predict
    result = detector.predict(features)
    
    return result[0]

@app.get("/recent-metrics/{device_id}")
def get_recent_metrics(device_id: str, limit: int = 100):
    metrics = list(metrics_collection.find({"device_id": device_id}).sort("timestamp", -1).limit(limit))
    return metrics

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
