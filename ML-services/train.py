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
import numpy as np
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
    try:
        client = pymongo.MongoClient("mongodb://localhost:27017/", serverSelectionTimeoutMS=5000)
        metrics = list(client.network_monitor.trafficmetrics.find().sort("timestamp", -1).limit(10000))
        if metrics and len(metrics) > 24:  # Need at least 24 samples for LSTM
            df = pd.DataFrame(metrics)
            features = preprocessor.snmp_features(df)
            lstm = LSTMAutoencoder()
            lstm.train(features.values)  # Pass raw 2D data, let prepare_sequences handle reshaping
        else:
            print("⚠️  Not enough data in MongoDB for LSTM training (need > 24 samples). Skipping LSTM training.")
    except Exception as e:
        print(f"⚠️  Could not train LSTM: {e}. Skipping LSTM training.")
    
    print("✅ Models trained and saved!")
