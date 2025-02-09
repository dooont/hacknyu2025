from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from bson import ObjectId
from typing import List, Optional, Dict
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv
from transformers import TextClassificationPipeline, AutoModelForSequenceClassification, AutoTokenizer
import aiohttp
import asyncio
from datetime import timedelta

load_dotenv()
MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("DB_NAME")
COLLECTION_NAME = os.getenv("COLLECTION_NAME")
COINGECKO_API_URL = "https://api.coingecko.com/api/v3"

app = FastAPI(title="Crypto Sentiment API")

client = AsyncIOMotorClient(MONGO_URI)
db = client[DB_NAME]
collection = db[COLLECTION_NAME]

class TweetData(BaseModel):
    tweet: str
    followC: int
    likeC: int
    viewC: int
    date: datetime
    coinType: List[str]

class SentimentData(BaseModel):
    id: str = Field(alias="_id")
    type: str
    coefficient: float
    followC: int
    likeC: int
    viewC: int
    date: datetime
    coinType: List[str]
    market_data: Optional[Dict] = None

    class Config:
        json_encoders = {ObjectId: str}

class CoinGeckoAPI:
    def __init__(self):
        self.session = None
        self.base_url = COINGECKO_API_URL
        
    async def init_session(self):
        if self.session is None:
            self.session = aiohttp.ClientSession()
            
    async def close_session(self):
        if self.session:
            await self.session.close()
            self.session = None
            
    async def get_coin_data(self, coin_id: str) -> Dict:
        await self.init_session()
        try:
            async with self.session.get(f"{self.base_url}/coins/{coin_id}") as response:
                if response.status == 429:
                    raise HTTPException(status_code=429, detail="Rate limit exceeded")
                elif response.status != 200:
                    raise HTTPException(status_code=response.status, detail="CoinGecko API error")
                data = await response.json()
                return {
                    "current_price": data["market_data"]["current_price"]["usd"],
                    "market_cap": data["market_data"]["market_cap"]["usd"],
                    "volume_24h": data["market_data"]["total_volume"]["usd"],
                    "price_change_24h": data["market_data"]["price_change_percentage_24h"]
                }
        except aiohttp.ClientError as e:
            raise HTTPException(status_code=500, detail=f"Error fetching coin data: {str(e)}")

coingecko = CoinGeckoAPI()

@app.on_event("startup")
async def startup_event():
    global pipe
    try:
        tokenizer = AutoTokenizer.from_pretrained("ElKulako/cryptobert", use_fast=True)
        model = AutoModelForSequenceClassification.from_pretrained("ElKulako/cryptobert", num_labels=3)
        pipe = TextClassificationPipeline(
            model=model,
            tokenizer=tokenizer,
            max_length=64,
            truncation=True,
            padding='max_length'
        )
    except Exception as e:
        print(f"Error loading model: {str(e)}")
        raise HTTPException(status_code=500, detail="Model loading failed")

@app.on_event("shutdown")
async def shutdown_event():
    await coingecko.close_session()

def map_coin_to_coingecko_id(coin_type: str) -> str:
    # Add more mappings as needed
    coin_mappings = {
        "BTC": "bitcoin",
        "ETH": "ethereum",
        "DOGE": "dogecoin",
        "ADA": "cardano",
        "SOL": "solana",
        "DOT": "polkadot",
        "AVAX": "avalanche-2",
        "MATIC": "matic-network",
        "LINK": "chainlink",
        "UNI": "uniswap"
    }
    return coin_mappings.get(coin_type.upper())

@app.post("/analyze", response_model=dict)
async def analyze_tweet(data: TweetData):
    try:
        prediction = pipe(data.tweet)[0]
        
        # Get market data for each coin type
        market_data = {}
        for coin in data.coinType:
            coingecko_id = map_coin_to_coingecko_id(coin)
            if coingecko_id:
                try:
                    market_data[coin] = await coingecko.get_coin_data(coingecko_id)
                except HTTPException as e:
                    if e.status_code != 429:  # Continue if not rate limited
                        market_data[coin] = {"error": str(e.detail)}
        
        sentiment_data = {
            "type": prediction["label"],
            "coefficient": float(prediction["score"]),
            "followC": data.followC,
            "likeC": data.likeC,
            "viewC": data.viewC,
            "date": data.date.astimezone(timezone.utc).isoformat(),
            "coinType": data.coinType,
            "market_data": market_data
        }

        result = await collection.insert_one(sentiment_data)
        sentiment_data["_id"] = str(result.inserted_id)

        return {"message": "Sentiment data saved successfully", "data": sentiment_data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/sentiments", response_model=List[SentimentData])
async def get_sentiments():
    try:
        sentiments = await collection.find().to_list(length=100)
        for sentiment in sentiments:
            sentiment["_id"] = str(sentiment["_id"])
        return sentiments
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/coin/{coin_id}/market-data")
async def get_coin_market_data(coin_id: str):
    try:
        coingecko_id = map_coin_to_coingecko_id(coin_id)
        if not coingecko_id:
            raise HTTPException(status_code=400, detail="Unsupported coin type")
        
        market_data = await coingecko.get_coin_data(coingecko_id)
        return {"coin_id": coin_id, "market_data": market_data}
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/supported-coins")
async def get_supported_coins():
    coin_mappings = {
        "BTC": "Bitcoin",
        "ETH": "Ethereum",
        "DOGE": "Dogecoin",
        "ADA": "Cardano",
        "SOL": "Solana",
        "DOT": "Polkadot",
        "AVAX": "Avalanche",
        "MATIC": "Polygon",
        "LINK": "Chainlink",
        "UNI": "Uniswap"
    }
    return {"supported_coins": coin_mappings}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}