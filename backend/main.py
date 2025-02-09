from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from bson import ObjectId
from typing import List
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv
from transformers import TextClassificationPipeline, AutoModelForSequenceClassification, AutoTokenizer

load_dotenv()
MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("DB_NAME")
COLLECTION_NAME = os.getenv("COLLECTION_NAME")

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
        print(f"Error loading model: {str(e)}")
        raise HTTPException(status_code=500, detail="Model loading failed")

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

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
