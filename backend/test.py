import requests
import json

def test_api():
    url = "http://localhost:8000/predict"
    
    test_data = {
        "texts": [
            "Bitcoin is looking very bullish today, breaking above 50k resistance!",
            "This crypto market is crashing hard, everything is going down",
            "No major price movement today, market seems stable"
        ]
    }
    
    response = requests.post(url, json=test_data)
    print(json.dumps(response.json(), indent=2))

if __name__ == "__main__":
    test_api()