from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
import numpy as np
from datetime import datetime
import math
from sentiment_analyzer import CryptoSentimentAnalyzer, SentimentConfig

@dataclass
class PriceRange:
    min_price: float
    max_price: float
    confidence: float

@dataclass
class TimeframePrediction:
    timeframe: str
    price_range: PriceRange
    sentiment_strength: float
    volume_impact: float
    market_volatility: float

class PricePredictionEngine:
    def __init__(self, volatility_window: int = 30):
        self.volatility_window = volatility_window
        
        # Confidence scaling factors
        self.sentiment_weight = 0.6
        self.volume_weight = 0.2
        self.volatility_weight = 0.2
        
        # Prediction ranges (as percentage of current price)
        self.range_multipliers = {
            '1d': {
                'high_impact': (0.05, 0.15),
                'medium_impact': (0.02, 0.08),
                'low_impact': (0.01, 0.03)
            },
            '7d': {
                'high_impact': (0.15, 0.45),
                'medium_impact': (0.08, 0.25),
                'low_impact': (0.03, 0.12)
            }
        }
    
    def calculate_volatility(self, historical_prices: List[float]) -> float:
        """Calculate price volatility using standard deviation of returns"""
        if len(historical_prices) < 2:
            return 0.0
        
        returns = np.diff(historical_prices) / historical_prices[:-1]
        return np.std(returns)
    
    def estimate_volume_impact(self, 
                             current_volume: float,
                             avg_volume: float,
                             sentiment_strength: float) -> float:
        """Estimate market impact based on volume and sentiment"""
        volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1.0
        return min(1.0, volume_ratio * abs(sentiment_strength))
    
    def get_impact_level(self, sentiment_strength: float, 
                        volume_impact: float, 
                        volatility: float) -> str:
        """Determine the overall market impact level"""
        weighted_impact = (
            sentiment_strength * self.sentiment_weight +
            volume_impact * self.volume_weight +
            volatility * self.volatility_weight
        )
        
        if weighted_impact > 0.7:
            return 'high_impact'
        elif weighted_impact > 0.4:
            return 'medium_impact'
        else:
            return 'low_impact'
    
    def calculate_confidence(self, 
                           sentiment_strength: float,
                           volume_impact: float,
                           volatility: float,
                           timeframe: str) -> float:
        """Calculate prediction confidence based on multiple factors"""
        base_confidence = sentiment_strength * self.sentiment_weight
        
        # Adjust confidence based on timeframe
        timeframe_factor = 1.0 if timeframe == '1d' else 0.7
        
        # Volume impact affects confidence
        volume_confidence = volume_impact * self.volume_weight
        
        # Higher volatility reduces confidence
        volatility_factor = math.exp(-volatility * 2) * self.volatility_weight
        
        total_confidence = (base_confidence + volume_confidence + volatility_factor) * timeframe_factor
        
        return max(0.0, min(1.0, total_confidence))
    
    def predict_price_range(self,
                          current_price: float,
                          sentiment_data: Dict,
                          market_data: Dict) -> Dict[str, TimeframePrediction]:
        """Predict price ranges for different timeframes"""
        
        # Extract relevant metrics
        sentiment_strength = abs(sentiment_data['average_sentiment'])
        trend_strength = abs(sentiment_data.get('trend_strength', 0))
        
        # Calculate market metrics
        volatility = self.calculate_volatility(market_data['historical_prices'])
        volume_impact = self.estimate_volume_impact(
            market_data['current_volume'],
            market_data['average_volume'],
            sentiment_strength
        )
        
        predictions = {}
        for timeframe in ['1d', '7d']:
            # Determine impact level
            impact_level = self.get_impact_level(sentiment_strength, volume_impact, volatility)
            
            # Get price range multipliers
            min_mult, max_mult = self.range_multipliers[timeframe][impact_level]
            
            # Adjust multipliers based on sentiment direction
            if sentiment_data['average_sentiment'] < 0:
                min_mult, max_mult = -max_mult, -min_mult
            
            # Calculate price range
            price_change_min = current_price * min_mult
            price_change_max = current_price * max_mult
            
            # Calculate confidence
            confidence = self.calculate_confidence(
                sentiment_strength,
                volume_impact,
                volatility,
                timeframe
            )
            
            predictions[timeframe] = TimeframePrediction(
                timeframe=timeframe,
                price_range=PriceRange(
                    min_price=current_price + price_change_min,
                    max_price=current_price + price_change_max,
                    confidence=confidence
                ),
                sentiment_strength=sentiment_strength,
                volume_impact=volume_impact,
                market_volatility=volatility
            )
        
        return predictions

class EnhancedCryptoAnalyzer:
    def __init__(self):
        self.sentiment_analyzer = CryptoSentimentAnalyzer()
        self.price_predictor = PricePredictionEngine()
    
    async def analyze_with_price_predictions(self,
                                          tweet_data: Dict,
                                          market_data: Dict) -> Dict:
        """Combine sentiment analysis with price predictions"""
        # Get sentiment analysis
        sentiment_scores = self.sentiment_analyzer.process_sentiment_data(tweet_data)
        coin_analysis = self.sentiment_analyzer.get_coin_analysis()
        
        # Generate price predictions for each coin
        predictions = {}
        for coin in tweet_data['coinType']:
            if coin in coin_analysis and coin in market_data:
                predictions[coin] = self.price_predictor.predict_price_range(
                    current_price=market_data[coin]['current_price'],
                    sentiment_data=coin_analysis[coin],
                    market_data=market_data[coin]
                )
        
        return {
            "sentiment_analysis": coin_analysis,
            "price_predictions": predictions
        }

async def analyze_tweet_sentiment(tweet_data: Dict, market_data: Dict) -> Dict:
    """Analyze a single tweet - for FastAPI endpoint"""
    analyzer = EnhancedCryptoAnalyzer()
    return await analyzer.analyze_with_price_predictions(tweet_data, market_data)