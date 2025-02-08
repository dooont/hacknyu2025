from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
from transformers import TextClassificationPipeline, AutoModelForSequenceClassification, AutoTokenizer

# Initialize FastAPI app
app = FastAPI(title="CryptoBERT API")

# Model configuration
MODEL_NAME = "ElKulako/cryptobert"

class TextInput(BaseModel):
    texts: List[str]

class SentimentResponse(BaseModel):
    text: str
    sentiment: str
    score: float

# Load model and create pipeline
@app.on_event("startup")
async def load_model():
    global pipe
    try:
        tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME, use_fast=True)
        model = AutoModelForSequenceClassification.from_pretrained(MODEL_NAME, num_labels=3)
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

@app.post("/predict", response_model=List[SentimentResponse])
async def predict_sentiment(input_data: TextInput):
    try:
        predictions = pipe(input_data.texts)
        
        results = []
        for text, pred in zip(input_data.texts, predictions):
            results.append(
                SentimentResponse(
                    text=text,
                    sentiment=pred['label'],
                    score=float(pred['score'])
                )
            )
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    return {"status": "healthy"}