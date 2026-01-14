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
            joblib.dump(self.model, 'models/anomaly_detector.joblib')

        def predict(self, X):
            """Predict anomalies"""
            X_scaled =  self.preprocessor.scaler.transform(X)
            predictions = self.model.predict(X_scaled)
            scores = self.model.decisio_function(X_scaled)

            return [{
                'is_anomaly': pred == -1,
                'anomaly_score': score[0], # higher means more normal
                'features': X.iloc[i].to_dict()
            } for pred, score in zip(predictions, scores)]
        
        def load(self):
            """Load the trained model from disk"""
            self.model = joblib.load('models/anomaly_detector.joblib')