"""
Preprocessing module for network monitoring ML services.

This module provides utilities for feature engineering and data preprocessing
for machine learning models used in network anomaly detection and monitoring.
It includes transformations for SNMP metrics and preparation of the NSL-KDD dataset.
"""

import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler, LabelEncoder
import joblib
from pathlib import Path

class NetworkPreprocessor:
    """
    A preprocessor class for network monitoring data.

    This class handles feature engineering for SNMP metrics and preprocessing
    of intrusion detection datasets like NSL-KDD. It provides methods to transform
    raw network data into features suitable for machine learning models.
    """

    def __init__(self):
        """
        Initialize the NetworkPreprocessor.

        Sets up the StandardScaler for feature scaling and a dictionary to store
        label encoders for categorical features.
        """
        self.scaler = StandardScaler()
        self.label_encoders = {}

    def snmp_features(self, metrics_df):
        """
        Transform raw SNMP metrics into machine learning features.

        This method processes time-series SNMP data by calculating rates, ratios,
        rolling statistics, and temporal features to create a feature set suitable
        for anomaly detection models.

        Args:
            metrics_df (pd.DataFrame): DataFrame containing raw SNMP metrics with
                columns like 'timestamp', 'device_id', 'packets_in', 'bytes_in',
                'bytes_out', 'packets_dropped', 'cpu_usage', 'latency_ms'.

        Returns:
            pd.DataFrame: Processed DataFrame with engineered features.
        """
        df = metrics_df.copy()

        # Convert timestamp to datetime and sort by device and time for time-series analysis
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.sort_values(['device_id', 'timestamp'])

        # Calculate rate features: packets and bytes per second based on 30-second polling intervals
        df['packets_per-sec'] = df.groupby('device_id')['packets_in'].diff().fillna(0) / 30  # 30s polling interval
        df['bytes_per_sec'] = df.groupby('device_id')['bytes_in'].diff().fillna(0) / 30

        # Calculate ratio features: byte output/input ratio and packet drop error rate
        df['byte_ratio'] = df['bytes_out'] / (df['bytes_in'] + 1)  # Add 1 to avoid division by zero
        df['error_rate'] = df['packets_dropped'] / (df['packets_in'] + 1)

        # Compute rolling aggregates over 5-minute windows (10 polls at 30s each)
        df['rolling_avg_cpu'] = df.groupby('device_id')['cpu_usage'].transform(lambda x: x.rolling(10, min_periods=1).mean()).bfill()
        df['rolling_avg_latency'] = df.groupby('device_id')['latency_ms'].transform(lambda x: x.rolling(10, min_periods=1).std()).bfill()

        # Extract temporal features: hour of day and day of week for cyclical patterns
        df['hour'] = df['timestamp'].dt.hour
        df['day_of_week'] = df['timestamp'].dt.dayofweek

        # Select the final set of features for model input
        features = [
            'packets_per-sec', 'bytes_per_sec', 'byte_ratio', 'error_rate',
            'rolling_avg_cpu', 'rolling_avg_latency', 'hour', 'day_of_week'
        ]

        return df[features].fillna(0)
    
    def prepare_nsl_kdd(self, train_path, test_path):
        """
        Load and preprocess the NSL-KDD intrusion detection dataset.

        This method loads the NSL-KDD dataset from CSV files, encodes categorical features,
        separates features and labels, scales the features, and saves the scaler for later use.
        The dataset is used for training anomaly detection models.

        Args:
            train_path (str): File path to the training dataset CSV.
            test_path (str): File path to the testing dataset CSV.

        Returns:
            tuple: (X_train_scaled, X_test_scaled, y_train) where
                - X_train_scaled: Scaled training features (numpy array)
                - X_test_scaled: Scaled testing features (numpy array)
                - y_train: Binary labels for training (1 for anomaly, 0 for normal)
        """
        # Define column names for NSL-KDD dataset (41 features + label + difficulty level)
        columns = (['duration', 'protocol_type', 'service', 'flag', 'src_bytes', 'dst_bytes', 'land',
                    'wrong_fragment', 'urgent', 'hot', 'num_failed_logins', 'logged_in', 'num_compromised',
                    'root_shell', 'su_attempted', 'num_root', 'num_file_creations', 'num_shells',
                    'num_access_files', 'num_outbound_cmds', 'is_host_login', 'is_guest_login', 'count',
                    'srv_count', 'serror_rate', 'srv_serror_rate', 'rerror_rate', 'srv_rerror_rate',
                    'same_srv_rate', 'diff_srv_rate', 'srv_diff_host_rate', 'dst_host_count',
                    'dst_host_srv_count', 'dst_host_same_srv_rate', 'dst_host_diff_srv_rate',
                    'dst_host_same_src_port_rate', 'dst_host_srv_diff_host_rate', 'dst_host_serror_rate',
                    'dst_host_srv_serror_rate', 'dst_host_rerror_rate', 'dst_host_srv_rerror_rate',
                    'label', 'difficulty'])

        # Load training and testing datasets with specified column names
        train = pd.read_csv(train_path, names=columns)
        test = pd.read_csv(test_path, names=columns)

        # Encode categorical features using LabelEncoder fitted on combined train/test data
        for col in ['protocol_type', 'service', 'flag']:
            le = LabelEncoder()
            combined = pd.concat([train[col], test[col]])
            le.fit(combined)
            train[col] = le.transform(train[col])
            test[col] = le.transform(test[col])

        # Separate features and labels: exclude 'label' and 'difficulty' columns from features
        X_train = train.drop(['label', 'difficulty'], axis=1)
        X_test = test.drop(['label', 'difficulty'], axis=1)
        # Create binary labels: 1 for anomaly (not 'normal'), 0 for normal
        y_train = (train['label'] != 'normal').astype(int)

        # Scale features using StandardScaler fitted on training data
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)

        # Save the fitted scaler to disk for future use in inference
        joblib.dump(self.scaler, Path('Models/nsl_kdd_scaler.pkl'))

        return X_train_scaled, X_test_scaled, y_train

# dont forget the check if the train and test path for the csv file is present in the code '''