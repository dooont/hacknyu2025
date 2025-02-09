import requests

data = {
    "tweet": "Bitcoin is on fire! It's going to the moon!",
    "followC": 1200,
    "likeC": 450,
    "viewC": 5000,
    "date": "2025-02-08T14:30:00Z",
    "coinType": ["Bitcoin", "BTC"]
}

response = requests.post("http://localhost:8000/analyze", json=data)
print(response.json())