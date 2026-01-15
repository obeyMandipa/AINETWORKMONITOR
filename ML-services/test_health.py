import requests
import json

# Test ML services health
try:
    print("Testing ML services health...")
    response = requests.get('http://localhost:8000/health', timeout=5)
    print(f"Health status: {response.status_code}")
    print(f"Response: {response.json()}")
except Exception as e:
    print(f"ML services error: {e}")

# Test prediction
try:
    print("\nTesting prediction...")
    data = {
        "device_id": "router1",
        "bytes_in": 1250000,
        "bytes_out": 987654,
        "packets_in": 5432,
        "packets_dropped": 12,
        "cpu_usage": 25,
        "latency_ms": 28.5
    }
    response = requests.post('http://localhost:8000/predict', json=data, timeout=10)
    print(f"Prediction status: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Prediction error: {e}")
