from datetime import datetime
import math
from typing import Dict, List, Optional
from pydantic import BaseModel

class SentimentConfig(BaseModel):
    """Configuration for sentiment analysis weights"""
    
    # Main component weights (should sum to 1)
    SENTIMENT_WEIGHT: float = 0.6
    ENGAGEMENT_WEIGHT: float = 0.4
    
    # Engagement metric weights (should sum to 1)
    FOLLOW_WEIGHT: float = 0.3
    LIKE_WEIGHT: float = 0.4
    VIEW_WEIGHT: float = 0.3
    
    # Time decay configuration
    TIME_DECAY_ALPHA: float = 0.1
    MAX_DAYS_OLD: int = 7

class CryptoSentimentAnalyzer:
    def __init__(self, config: Optional[SentimentConfig] = None):
        self.config = config or SentimentConfig()
        self.aggregator: Dict[str, Dict] = {}
    
    def normalize_engagement_metric(self, value: float) -> float:
        """Normalize engagement metrics using log scaling"""
        if value <= 0:
            return 0
        return math.log1p(value) / math.log1p(value * 2)
    
    def calculate_time_decay(self, date: datetime) -> float:
        """Calculate time decay factor based on signal age"""
        time_diff_days = (datetime.now() - date).total_seconds() / 86400.0
        if time_diff_days > self.config.MAX_DAYS_OLD:
            return 0
        return math.exp(-self.config.TIME_DECAY_ALPHA * time_diff_days)
    
    def calculate_engagement_score(self, follow_count: int, like_count: int, 
                                 view_count: int) -> float:
        """Calculate weighted engagement score"""
        norm_follows = self.normalize_engagement_metric(follow_count)
        norm_likes = self.normalize_engagement_metric(like_count)
        norm_views = self.normalize_engagement_metric(view_count)
        
        return (
            norm_follows * self.config.FOLLOW_WEIGHT +
            norm_likes * self.config.LIKE_WEIGHT +
            norm_views * self.config.VIEW_WEIGHT
        )
    
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
        sentiment_type = data["type"]
        coefficient = float(data["coefficient"])
        date = data["date"]
        
        sentiment_value = self.map_sentiment_to_value(sentiment_type, coefficient)
        time_decay = self.calculate_time_decay(date)
        
        if time_decay == 0:
            return {}
        
        engagement_score = self.calculate_engagement_score(
            data["followC"],
            data["likeC"],
            data["viewC"]
        )
        
        final_score = (
            sentiment_value * self.config.SENTIMENT_WEIGHT +
            engagement_score * self.config.ENGAGEMENT_WEIGHT
        ) * time_decay
        
        results = {}
        for coin in data["coinType"]:
            self._update_aggregator(coin, final_score, date)
            results[coin] = final_score
        
        return results
    
    def _update_aggregator(self, coin: str, score: float, date: datetime):
        """Update aggregator with new sentiment data"""
        if coin not in self.aggregator:
            self.aggregator[coin] = {
                "positive_count": 0,
                "negative_count": 0,
                "neutral_count": 0,
                "total_sentiment": 0.0,
                "weighted_volume": 0.0,
                "recent_signals": []
            }
        
        if score > 0:
            self.aggregator[coin]["positive_count"] += 1
        elif score < 0:
            self.aggregator[coin]["negative_count"] += 1
        else:
            self.aggregator[coin]["neutral_count"] += 1
        
        self.aggregator[coin]["total_sentiment"] += score
        self.aggregator[coin]["weighted_volume"] += abs(score)
        
        self.aggregator[coin]["recent_signals"].append({
            "score": score,
            "timestamp": date
        })
        
        # Keep only recent signals
        self.aggregator[coin]["recent_signals"] = [
            signal for signal in self.aggregator[coin]["recent_signals"]
            if (datetime.now() - signal["timestamp"]).days <= self.config.MAX_DAYS_OLD
        ]
    
    def calculate_trend_strength(self, signals: List[Dict]) -> float:
        """Calculate trend strength based on recent signals"""
        if not signals:
            return 0.0
        
        # Weight more recent signals higher
        total_weighted_score = 0.0
        total_weight = 0.0
        
        for i, signal in enumerate(sorted(signals, key=lambda x: x["timestamp"])):
            weight = math.exp(i / len(signals))  # Exponential weighting
            total_weighted_score += signal["score"] * weight
            total_weight += weight
        
        return total_weighted_score / total_weight if total_weight > 0 else 0.0
    
    def get_coin_analysis(self) -> Dict[str, Dict]:
        """Get analysis results for all coins"""
        results = {}
        for coin, data in self.aggregator.items():
            total_signals = (
                data["positive_count"] +
                data["negative_count"] +
                data["neutral_count"]
            )
            
            if total_signals == 0:
                continue
            
            avg_sentiment = data["total_sentiment"] / total_signals
            sentiment_volume = data["weighted_volume"] / total_signals
            trend_strength = self.calculate_trend_strength(data["recent_signals"])
            
            # Calculate agreement ratio
            max_count = max(
                data["positive_count"],
                data["negative_count"],
                data["neutral_count"]
            )
            agreement_ratio = max_count / total_signals
            
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
                }
            }
        
        return results
    
    def reset_aggregator(self):
        """Reset the aggregator for new analysis"""
        self.aggregator = {}