import requests
import json
from datetime import datetime
import time

BASE_URL = "http://localhost:8000"  # Adjust if your API is running on a different port

def test_health():
    response = requests.get(f"{BASE_URL}/health")
    print("\nHealth Check:")
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")

def test_supported_coins():
    response = requests.get(f"{BASE_URL}/supported-coins")
    print("\nSupported Coins:")
    print(f"Status Code: {response.status_code}")
    print(json.dumps(response.json(), indent=2))

def test_coin_market_data(coin_id="BTC"):
    response = requests.get(f"{BASE_URL}/coin/{coin_id}/market-data")
    print(f"\nMarket Data for {coin_id}:")
    print(f"Status Code: {response.status_code}")
    print(json.dumps(response.json(), indent=2))

def test_analyze_tweet():
    tweet_data = {
        "tweet": "Bitcoin is looking very bullish today! #BTC",
        "followC": 1000,
        "likeC": 500,
        "viewC": 10000,
        "date": datetime.now().isoformat(),
        "coinType": ["BTC"]
    }
    
    response = requests.post(f"{BASE_URL}/analyze", json=tweet_data)
    print("\nAnalyze Tweet:")
    print(f"Status Code: {response.status_code}")
    print(json.dumps(response.json(), indent=2))

def test_get_sentiments():
    response = requests.get(f"{BASE_URL}/sentiments")
    print("\nGet Sentiments:")
    print(f"Status Code: {response.status_code}")
    print(json.dumps(response.json(), indent=2))

def run_all_tests():
    print("Starting API Tests...")
    
    # Basic health check
    test_health()
    
    # Get supported coins
    test_supported_coins()
    
    # Test market data for different coins
    for coin in ["BTC", "ETH", "DOGE"]:
        test_coin_market_data(coin)
        time.sleep(1)  # Avoid rate limiting
    
    # Test sentiment analysis
    test_analyze_tweet()
    
    # Test getting sentiments
    test_get_sentiments()

if __name__ == "__main__":
    run_all_tests()