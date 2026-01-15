# Anomaly detection
"""
This module defines an Isolation Forest model for detecting anomalies
in network monitoring data. It includes methods for training, predicting, 
and saving/loading the model.
"""


from sklearn.ensemble import IsolationForest
import joblib 
import numpy as np
from preprocess import NetworkPreprocessor

class AnomalyDetector:
    """
    Anomaly detection model using Isolation Forest.

    This class encapsulates the Isolation Forest model for detecting anomalies
    in network monitoring data. It includes methods for training, predicting,
    and saving/loading the model.
    """

    def __init__(self):
        """
        Initialize the AnomalyDetector.

        Sets up the Isolation Forest model with predefined parameters.
        """
        self.model = IsolationForest(contamination=0.01, random_state=42)
        self.preprocessor = NetworkPreprocessor()

    def train(self, X_train):
        """Train on normal traffic patterns"""
        self.model.fit(X_train)
        joblib.dump(self.model, 'Models/anomaly_detector.joblib')

    def predict(self, X):
        """Predict anomalies"""
        # Note: Isolation Forest doesn't require scaling, but we keep the structure for consistency
        # If X is a DataFrame, convert to numpy
        if hasattr(X, 'values'):
            X_array = X.values
        else:
            X_array = X
        
        predictions = self.model.predict(X_array)
        scores = self.model.decision_function(X_array)

        return [{
            'is_anomaly': pred == -1,
            'anomaly_score': float(score), # higher means more normal
            'threshold': -0.5
        } for pred, score in zip(predictions, scores)]
    
    def load(self):
        """Load the trained model from disk"""
        self.model = joblib.load('Models/anomaly_detector.joblib')