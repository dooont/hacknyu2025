#!/bin/bash

# Text colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored messages
print_message() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

print_message $GREEN "🚀 Starting CryptoBERT API installation process..."

# Check Python version
if ! command_exists python3; then
    print_message $RED "❌ Python 3 is not installed. Please install Python 3.11 or later."
    exit 1
fi

# Get Python version
PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
print_message $YELLOW "📌 Detected Python version: $PYTHON_VERSION"

# Check if pip is installed
if ! command_exists pip3; then
    print_message $RED "❌ pip3 is not installed. Please install pip3 first."
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    print_message $YELLOW "🔧 Creating virtual environment..."
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        print_message $RED "❌ Failed to create virtual environment"
        exit 1
    fi
else
    print_message $GREEN "✅ Virtual environment already exists"
fi

# Activate virtual environment
print_message $YELLOW "🔧 Activating virtual environment..."
source venv/bin/activate
if [ $? -ne 0 ]; then
    print_message $RED "❌ Failed to activate virtual environment"
    exit 1
fi

# Upgrade pip
print_message $YELLOW "🔄 Upgrading pip..."
python3 -m pip install --upgrade pip
if [ $? -ne 0 ]; then
    print_message $RED "❌ Failed to upgrade pip"
    exit 1
fi

# Install required packages
print_message $YELLOW "📦 Installing required packages..."

# Create requirements.txt if it doesn't exist
if [ ! -f "requirements.txt" ]; then
    echo "fastapi==0.104.1
uvicorn==0.24.0
transformers==4.35.2
torch
pydantic==2.4.2" > requirements.txt
fi

# Install packages
python3 -m pip install -r requirements.txt
if [ $? -ne 0 ]; then
    print_message $RED "❌ Failed to install required packages"
    exit 1
fi

# Create main.py if it doesn't exist
if [ ! -f "main.py" ]; then
    print_message $YELLOW "📝 Creating main.py..."
    echo 'from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
from transformers import TextClassificationPipeline, AutoModelForSequenceClassification, AutoTokenizer

app = FastAPI(title="CryptoBERT API")
MODEL_NAME = "ElKulako/cryptobert"

class TextInput(BaseModel):
    texts: List[str]

class SentimentResponse(BaseModel):
    text: str
    sentiment: str
    score: float

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
            padding="max_length"
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
                    sentiment=pred["label"],
                    score=float(pred["score"])
                )
            )
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    return {"status": "healthy"}' > main.py
fi

# Create test file if it doesn't exist
if [ ! -f "test_api.py" ]; then
    print_message $YELLOW "📝 Creating test_api.py..."
    echo 'import requests
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
    
    try:
        response = requests.post(url, json=test_data)
        print(json.dumps(response.json(), indent=2))
    except requests.exceptions.ConnectionError:
        print("Error: Cannot connect to the server. Make sure the server is running.")

if __name__ == "__main__":
    test_api()' > test_api.py
fi

print_message $GREEN """
✨ Installation complete! ✨

To start using the CryptoBERT API:

1. Activate the virtual environment (if not already activated):
   source venv/bin/activate
   
2. Run the server:
   python3 -m uvicorn main:app --reload

3. Test the API using test_api.py:
   python3 test_api.py

The API will be available at: http://localhost:8000
API documentation will be available at: http://localhost:8000/docs

Note: The first time you run the server, it will download the CryptoBERT model 
which may take a few minutes depending on your internet connection.
"""