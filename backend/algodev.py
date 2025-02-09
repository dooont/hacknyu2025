from datetime import datetime
import math
from typing import Dict, List, Optional
from pydantic import BaseModel

class SentimentConfig(BaseModel):
    """Configuration for sentiment analysis weights"""
    
    # Main component weights (should sum to 1)
    SENTIMENT_WEIGHT: float = 0.6  # Increased weight for sentiment due to scraped data
    ENGAGEMENT_WEIGHT: float = 0.4  # Decreased since engagement metrics might be less reliable
    
    # Engagement metric weights (should sum to 1)
    FOLLOW_WEIGHT: float = 0.3
    LIKE_WEIGHT: float = 0.4    # Increased weight for likes as they're often more reliable
    VIEW_WEIGHT: float = 0.3
    
    # Time decay configuration
    TIME_DECAY_ALPHA: float = 0.1
    MAX_DAYS_OLD: int = 7  # Maximum age of signals to consider

class CryptoSentimentAnalyzer:
    def __init__(self, config: Optional[SentimentConfig] = None):
        self.config = config or SentimentConfig()
        self.aggregator: Dict[str, Dict] = {}
    
    def normalize_engagement_metric(self, value: float) -> float:
        """Normalize engagement metrics using relative scaling"""
        if value <= 0:
            return 0
        return math.log1p(value) / math.log1p(value * 2)  # Normalizes between 0 and 1
    
    def calculate_time_decay(self, date: datetime) -> float:
        """Calculate time decay factor based on signal age"""
        time_diff_days = (datetime.now() - date).total_seconds() / 86400.0
        if time_diff_days > self.config.MAX_DAYS_OLD:
            return 0
        return math.exp(-self.config.TIME_DECAY_ALPHA * time_diff_days)
    
    def calculate_engagement_score(self, follow_count: int, like_count: int, 
                                 view_count: int) -> float:
        """Calculate weighted engagement score without minimum thresholds"""
        # Normalize each metric
        norm_follows = self.normalize_engagement_metric(follow_count)
        norm_likes = self.normalize_engagement_metric(like_count)
        norm_views = self.normalize_engagement_metric(view_count)
        
        # Calculate weighted engagement score
        engagement_score = (
            norm_follows * self.config.FOLLOW_WEIGHT +
            norm_likes * self.config.LIKE_WEIGHT +
            norm_views * self.config.VIEW_WEIGHT
        )
        
        return engagement_score
    
    def map_sentiment_to_value(self, sentiment_type: str, coefficient: float) -> float:
        """Map sentiment types to numerical values with confidence weighting"""
        base_sentiment = {
            "bullish": 1.0,
            "bearish": -1.0,
            "neutral": 0.0
        }.get(sentiment_type.lower(), 0.0)
        
        return base_sentiment * coefficient
    
    def process_sentiment_data(self, data: Dict) -> Dict[str, float]:
        """Process a single piece of sentiment data"""
        # Extract basic data
        sentiment_type = data["type"]
        coefficient = float(data["coefficient"])
        date = data["date"]
        
        # Calculate components
        sentiment_value = self.map_sentiment_to_value(sentiment_type, coefficient)
        time_decay = self.calculate_time_decay(date)
        
        if time_decay == 0:  # Skip if too old
            return {}
        
        engagement_score = self.calculate_engagement_score(
            data["followC"],
            data["likeC"],
            data["viewC"]
        )
        
        # Calculate final sentiment score
        final_score = (
            sentiment_value * self.config.SENTIMENT_WEIGHT +
            engagement_score * self.config.ENGAGEMENT_WEIGHT
        ) * time_decay
        
        # Prepare results for each coin
        results = {}
        for coin in data["coinType"]:
            results[coin] = final_score
            
            # Update aggregator
            if coin not in self.aggregator:
                self.aggregator[coin] = {
                    "positive_count": 0,
                    "negative_count": 0,
                    "neutral_count": 0,
                    "total_sentiment": 0.0,
                    "weighted_volume": 0.0,
                    "recent_signals": []
                }
            
            # Update counters
            if final_score > 0:
                self.aggregator[coin]["positive_count"] += 1
            elif final_score < 0:
                self.aggregator[coin]["negative_count"] += 1
            else:
                self.aggregator[coin]["neutral_count"] += 1
            
            self.aggregator[coin]["total_sentiment"] += final_score
            self.aggregator[coin]["weighted_volume"] += abs(final_score)
            
            self.aggregator[coin]["recent_signals"].append({
                "score": final_score,
                "timestamp": date
            })
            
            self.aggregator[coin]["recent_signals"] = [
                signal for signal in self.aggregator[coin]["recent_signals"]
                if (datetime.now() - signal["timestamp"]).days <= self.config.MAX_DAYS_OLD
            ]
        
        return results
    
    def calculate_trend_strength(self, signals: List[Dict]) -> float:
        if not signals:
            return 0.0
            
        total_weighted_score = 0.0
        total_weight = 0.0
        
        for i, signal in enumerate(sorted(signals, key=lambda x: x["timestamp"])):
            weight = math.exp(i / len(signals))  
            total_weighted_score += signal["score"] * weight
            total_weight += weight
            
        return total_weighted_score / total_weight if total_weight > 0 else 0.0
    
    def get_coin_analysis(self) -> Dict[str, Dict]:
        """Get final analysis for all coins"""
        results = {}
        for coin, data in self.aggregator.items():
            total_signals = data["positive_count"] + data["negative_count"] + data["neutral_count"]
            if total_signals == 0:
                continue
            
            # Calculate sentiment metrics
            avg_sentiment = data["total_sentiment"] / total_signals
            sentiment_volume = data["weighted_volume"] / total_signals
            trend_strength = self.calculate_trend_strength(data["recent_signals"])
            
            # Calculate agreement ratio (how consistent the signals are)
            dominant_direction = "positive" if data["positive_count"] > data["negative_count"] else "negative"
            if dominant_direction == "positive":
                agreement_ratio = data["positive_count"] / total_signals
            else:
                agreement_ratio = data["negative_count"] / total_signals
            
            results[coin] = {
                "average_sentiment": avg_sentiment,
                "sentiment_volume": sentiment_volume,
                "trend_strength": trend_strength,
                "agreement_ratio": agreement_ratio,
                "signal_counts": {
                    "positive": data["positive_count"],
                    "negative": data["negative_count"],
                    "neutral": data["neutral_count"],
                    "total": total_signals
                },
                "recommendation": {
                    "action": "buy" if avg_sentiment > 0.2 and trend_strength > 0 else
                             "sell" if avg_sentiment < -0.2 and trend_strength < 0 else
                             "hold",
                    "confidence": min(1.0, agreement_ratio * math.sqrt(total_signals) / 10)
                }
            }
        
        return results
    
    def reset_aggregator(self):
        """Reset the aggregator for new analysis"""
        self.aggregator = {}

async def analyze_tweet_sentiment(tweet_data: Dict) -> Dict:
    """Analyze a single tweet - for FastAPI endpoint"""
    analyzer = CryptoSentimentAnalyzer()
    sentiment_scores = analyzer.process_sentiment_data(tweet_data)
    
    return {
        "sentiment_scores": sentiment_scores,
        "coin_analysis": analyzer.get_coin_analysis()
    }

def run_batch_analysis(data_list: List[Dict]) -> Dict:
    """Run analysis on a batch of scraped data"""
    analyzer = CryptoSentimentAnalyzer()
    
    for item in data_list:
        analyzer.process_sentiment_data(item)
    
    return analyzer.get_coin_analysis()