import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timezone
import asyncio
from unittest.mock import patch, Mock
from main import app, CoinGeckoAPI

client = TestClient(app)

# Mock data for testing
sample_tweet_data = {
    "tweet": "Bitcoin is looking very bullish today! #BTC",
    "followC": 1000,
    "likeC": 500,
    "viewC": 10000,
    "date": datetime.now().isoformat(),
    "coinType": ["BTC"]
}

mock_coin_data = {
    "market_data": {
        "current_price": {"usd": 50000},
        "market_cap": {"usd": 1000000000},
        "total_volume": {"usd": 50000000},
        "price_change_percentage_24h": 5.5
    }
}

# Unit Tests
def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

def test_supported_coins():
    response = client.get("/supported-coins")
    assert response.status_code == 200
    data = response.json()
    assert "supported_coins" in data
    assert "BTC" in data["supported_coins"]
    assert "ETH" in data["supported_coins"]

@pytest.mark.asyncio
async def test_coin_market_data():
    with patch.object(CoinGeckoAPI, 'get_coin_data', return_value=mock_coin_data):
        response = client.get("/coin/BTC/market-data")
        assert response.status_code == 200
        data = response.json()
        assert "market_data" in data
        assert "current_price" in data["market_data"]

@pytest.mark.asyncio
async def test_analyze_tweet():
    with patch('main.pipe') as mock_pipe:
        mock_pipe.return_value = [{"label": "positive", "score": 0.95}]
        response = client.post("/analyze", json=sample_tweet_data)
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "data" in data
        assert data["data"]["type"] == "positive"

def test_invalid_coin():
    response = client.get("/coin/INVALID/market-data")
    assert response.status_code == 400
    assert "Unsupported coin type" in response.json()["detail"]