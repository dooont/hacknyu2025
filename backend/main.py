from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List
from datetime import datetime, timezone, timedelta
from motor.motor_asyncio import AsyncIOMotorClient
import os
import httpx
from dotenv import load_dotenv
from transformers import TextClassificationPipeline, AutoModelForSequenceClassification, AutoTokenizer
from bson import ObjectId

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("DB_NAME")
COLLECTION_NAME = os.getenv("COLLECTION_NAME")

# CoinPaprika historical endpoint for BTC
COINPAPRIKA_HISTORICAL_URL = "https://api.coinpaprika.com/v1/tickers/btc-bitcoin/historical"

app = FastAPI(title="Crypto Sentiment API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Adjust if needed
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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

    class Config:
        json_encoders = {ObjectId: str}

@app.on_event("startup")
async def load_model():
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
        raise HTTPException(status_code=500, detail=f"Model loading failed: {str(e)}")

@app.post("/analyze", response_model=dict)
async def analyze_tweet(data: TweetData):
    try:
        prediction = pipe(data.tweet)[0]
        sentiment_data = {
            "type": prediction["label"],
            "coefficient": float(prediction["score"]),
            "followC": data.followC,
            "likeC": data.likeC,
            "viewC": data.viewC,
            "date": data.date.astimezone(timezone.utc).isoformat(),
            "coinType": data.coinType
        }
        result = await collection.insert_one(sentiment_data)
        sentiment_data["_id"] = str(result.inserted_id)
        return {"message": "Sentiment data saved successfully", "data": sentiment_data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing tweet: {str(e)}")

@app.get("/sentiments", response_model=List[SentimentData])
async def get_sentiments():
    try:
        sentiments = await collection.find(
            {}, {"_id": 1, "type": 1, "coefficient": 1, "followC": 1, "likeC": 1, "viewC": 1, "date": 1, "coinType": 1}
        ).to_list(length=200)

        for s in sentiments:
            s["_id"] = str(s["_id"])

        return sentiments
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving sentiments: {str(e)}")

@app.get("/bitcoin-data")
async def get_bitcoin_data(days: int = 1):
    """
    CoinPaprika free plan constraints:
      - 1 day max hourly data
      - Up to 1 year (365 days) daily data
    We'll clamp 1 day to ~23h to be safe, and >1 day up to 364 to avoid partial intervals.
    If STILL 402 error, consider adjusting the clamping further or upgrading plan.
    Returns: { "prices": [ {time, price}, ... ] }
    """

    now_utc = datetime.utcnow()

    if days == 1:
        # For 1 day of data, clamp to 23 hours from "now" to avoid crossing the boundary
        end_dt = now_utc.replace(minute=0, second=0, microsecond=0)
        start_dt = end_dt - timedelta(hours=23)  # clamp to 23 hours
        url = (f"{COINPAPRIKA_HISTORICAL_URL}"
               f"?start={start_dt.strftime('%Y-%m-%dT%H:%M:%SZ')}"
               f"&end={end_dt.strftime('%Y-%m-%dT%H:%M:%SZ')}"
               f"&interval=1h")
    else:
        # daily data
        if days > 364:
            days = 364  # clamp max 1 year
        end_dt = now_utc.replace(hour=0, minute=0, second=0, microsecond=0)
        start_dt = end_dt - timedelta(days=days)

        # If they end up identical, shift end by 1 day to avoid zero-range
        if start_dt == end_dt:
            end_dt += timedelta(days=1)

        url = (f"{COINPAPRIKA_HISTORICAL_URL}"
               f"?start={start_dt.strftime('%Y-%m-%dT%H:%M:%SZ')}"
               f"&end={end_dt.strftime('%Y-%m-%dT%H:%M:%SZ')}"
               f"&interval=24h")

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url)

        print("[DEBUG] CoinPaprika Response:", response.status_code, response.text)

        if response.status_code != 200:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"CoinPaprika Error: {response.text}"
            )

        data = response.json()
        if not isinstance(data, list):
            raise HTTPException(status_code=500, detail="Invalid response: must be a list")

        formatted_data = []
        for entry in data:
            ts_str = entry["timestamp"]
            ts_obj = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
            if days == 1:
                # hourly
                time_str = ts_obj.strftime("%b %d, %H:%M")
            else:
                # daily
                time_str = ts_obj.strftime("%b %d, %Y")
            price = entry["price"]
            formatted_data.append({"time": time_str, "price": price})

        return {"prices": formatted_data}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching Bitcoin data: {str(e)}")


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
