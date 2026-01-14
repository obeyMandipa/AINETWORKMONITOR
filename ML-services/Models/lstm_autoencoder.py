# TIme series prediction
"""
Docstring for ML-services.Models.lstm_autoencoder
LSTM Autoencoder model for anomaly detection in network monitoring data.
This module defines an LSTM Autoencoder model for detecting anomalies
in time-series network monitoring data. It includes methods for building,
training, predicting, and saving/loading the model.
"""

from dbm import error
import tensorflow as tf
import numpy as np 
import joblib 
from preprocess import NetworkPreprocessor

class LSTMAutoencoder:
    """
    LSTM Autoencoder model for anomaly detection.

    This class encapsulates the LSTM Autoencoder model for detecting anomalies
    in time-series network monitoring data. It includes methods for building,
    training, predicting, and saving/loading the model.
    """

    def __init__(self, timesteps=24, features=8):
        """
        Initialize the LSTMAutoencoder.

        Sets up the LSTM Autoencoder architecture with specified parameters.
        """
        self.timesteps = timesteps
        self.n_features = features
        self.model = self.build_model()
        self.preprocessor = NetworkPreprocessor()

    def build_model(self):
        """Build the LSTM Autoencoder model architecture."""
        model = tf.keras.Sequential([
            tf.keras.layers.LSTM(64, return_sequences=True, input_shape=(self.timesteps, self.features)),
            tf.keras.layers.Dropout(0.2),
            tf.keras.layers.LSTM(32, return_sequences=True),
            tf.keras.layers.Dropout(0.2),
            tf.keras.layers.TimeDistributed(tf.keras.layers.Dense(16, activation='relu')),
            tf.keras.layers.LSTM(32, return_sequences=True),
            tf.keras.layers.Dropout(0.2),
            tf.keras.layers.LSTM(64, return_sequences=True),
            tf.keras.layers.TimeDistributed(tf.keras.layers.Dense(self.features))
        ])
        model.compile(optimizer='adam', loss='mse')
        return model
    
    def prepare_sequences(self, data):
        """Prepare sequences for LSTM input."""
        X = []
        for i in range(self.timesteps, len(data)):
            X.append(data[i-self.timesteps:i])
        return np.array(X)

    def train(self, train_data):
        """Train the LSTM Autoencoder on normal traffic patterns."""
        X_train = self.prepare_sequences(train_data)
        self.model.fit(X_train, X_train, epochs=50, batch_size=32, validation_split=0.1)
        self.model.save('models/lstm_anomaly.h5')

    def predict(self, data):
        """Predict anomalies using reconstruction error."""
        X_test = self.prepare_sequences(data)
        reconstructions = self.model.predict(X_test)
        mse = np.mean(np.power(X_test - reconstructions, 2), axis=(1,2))
        threshold = np.percentile(mse, 90)

        return {
            'is_anomaly': mse[0] > threshold,
            'anomaly_score': mse[0],
            'threshold': threshold
        } 
