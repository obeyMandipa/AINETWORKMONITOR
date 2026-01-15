# Training scripts train.py

"""
Docstring for ML-services.train
Train machine learning models for network anomaly detection.
This module provides scripts to train machine learning models such as
Isolation Forest and LSTM Autoencoder using preprocessed network monitoring data.

"""
from preprocess import NetworkPreprocessor
from Models.isolation_forest import AnomalyDetector
from Models.lstm_autoencoder import LSTMAutoencoder
import pandas as pd
import pymongo

if __name__ == "__main__":
    preprocessor = NetworkPreprocessor()
    
    # Train Isolation Forest
    print("Training Isolation Forest...")
    X_train, _, _ = preprocessor.prepare_nsl_kdd('data/raw/KDDTrain+.csv', 'data/raw/KDDTest+.csv')
    detector = AnomalyDetector()
    detector.train(X_train)
    
    # Train LSTM (use recent MongoDB data)
    print("Training LSTM...")
    client = pymongo.MongoClient("mongodb://localhost:27017/")
    metrics = list(client.network_monitor.trafficmetrics.find().sort("timestamp", -1).limit(10000))
    df = pd.DataFrame(metrics)
    features = preprocessor.snmp_features(df)
    lstm = LSTMAutoencoder()
    lstm.train(features.values.reshape(-1, 24, 8))
    
    print("✅ Models trained and saved!")
