import unittest
import asyncio
from datetime import datetime, timedelta
import numpy as np
from sentiment_analyzer import CryptoSentimentAnalyzer, SentimentConfig
from price_prediction import (
    PricePredictionEngine,
    EnhancedCryptoAnalyzer,
    PriceRange,
    TimeframePrediction
)

class TestSentimentAnalyzer(unittest.TestCase):
    def setUp(self):
        self.analyzer = CryptoSentimentAnalyzer()
        self.base_time = datetime.now()
        
        # Sample test data
        self.sample_tweet = {
            "type": "bullish",
            "coefficient": 0.85,
            "followC": 1000,
            "likeC": 500,
            "viewC": 5000,
            "date": self.base_time,
            "coinType": ["BTC", "ETH"]
        }
    
    def test_sentiment_mapping(self):
        test_cases = [
            ("bullish", 0.9, 0.9),
            ("bearish", 0.8, -0.8),
            ("neutral", 0.7, 0.0),
            ("invalid", 0.6, 0.0)
        ]
        
        for sentiment_type, coef, expected in test_cases:
            result = self.analyzer.map_sentiment_to_value(sentiment_type, coef)
            self.assertAlmostEqual(result, expected, places=2)
    
    def test_engagement_normalization(self):
        test_metrics = [0, 100, 1000, 10000]
        
        for metric in test_metrics:
            normalized = self.analyzer.normalize_engagement_metric(metric)
            self.assertTrue(0 <= normalized <= 1)
            
            if metric <= 0:
                self.assertEqual(normalized, 0)
    
    def test_time_decay(self):
        test_dates = [
            (self.base_time, 1.0),  # Now
            (self.base_time - timedelta(days=3), 0.74),  
            (self.base_time - timedelta(days=7), 0.50),  
            (self.base_time - timedelta(days=8), 0.0)   
        ]
        
        for date, expected_decay in test_dates:
            decay = self.analyzer.calculate_time_decay(date)
            self.assertAlmostEqual(decay, expected_decay, places=2)
    
    def test_engagement_score(self):
        test_cases = [
            (1000, 500, 5000, 0.3, 0.7),
            (0, 0, 0, 0.0, 0.0),
            (10000, 5000, 50000, 0.4, 0.8)
        ]
        
        for follows, likes, views, min_expected, max_expected in test_cases:
            score = self.analyzer.calculate_engagement_score(follows, likes, views)
            self.assertTrue(min_expected <= score <= max_expected)
    
    def test_process_sentiment_data(self):
        result = self.analyzer.process_sentiment_data(self.sample_tweet)
        
        self.assertIn("BTC", result)
        self.assertIn("ETH", result)
        self.assertTrue(result["BTC"] > 0)  
        
        bearish_tweet = self.sample_tweet.copy()
        bearish_tweet["type"] = "bearish"
        result = self.analyzer.process_sentiment_data(bearish_tweet)
        self.assertTrue(result["BTC"] < 0)  

class TestPricePrediction(unittest.TestCase):
    def setUp(self):
        self.predictor = PricePredictionEngine()
        self.current_price = 40000  
        
        self.market_data = {
            'historical_prices': [
                40000, 41000, 39500, 40500, 40800,
                39800, 40200, 41200, 40700, 40000
            ],
            'current_volume': 1000000,
            'average_volume': 800000
        }
        
        self.sentiment_data = {
            'average_sentiment': 0.75,
            'agreement_ratio': 0.8,
            'trend_strength': 0.65,
            'sentiment_volume': 0.9,
            'signal_counts': {
                'positive': 150,
                'negative': 30,
                'neutral': 20,
                'total': 200
            }
        }
    
    def test_volatility_calculation(self):
        volatility = self.predictor.calculate_volatility(self.market_data['historical_prices'])
        self.assertTrue(0 <= volatility <= 1)
        
        self.assertEqual(self.predictor.calculate_volatility([]), 0.0)
        self.assertEqual(self.predictor.calculate_volatility([100]), 0.0)
    
    def test_volume_impact(self):
        impact = self.predictor.estimate_volume_impact(
            self.market_data['current_volume'],
            self.market_data['average_volume'],
            self.sentiment_data['average_sentiment']
        )
        self.assertTrue(0 <= impact <= 1)
    
    def test_impact_level(self):
        test_cases = [
            (0.9, 0.8, 0.1, 'high_impact'),
            (0.5, 0.5, 0.5, 'medium_impact'),
            (0.2, 0.2, 0.2, 'low_impact')
        ]
        
        for sentiment, volume, volatility, expected in test_cases:
            level = self.predictor.get_impact_level(sentiment, volume, volatility)
            self.assertEqual(level, expected)
    
    def test_price_range_prediction(self):
        predictions = self.predictor.predict_price_range(
            self.current_price,
            self.sentiment_data,
            self.market_data
        )
        
        self.assertIn('1d', predictions)
        self.assertIn('7d', predictions)
        
        day_pred = predictions['1d']
        self.assertIsInstance(day_pred, TimeframePrediction)
        self.assertTrue(day_pred.price_range.min_price < day_pred.price_range.max_price)
        
        week_pred = predictions['7d']
        self.assertTrue(week_pred.price_range.confidence <= day_pred.price_range.confidence)

class TestEnhancedAnalyzer(unittest.TestCase):
    def setUp(self):
        self.analyzer = EnhancedCryptoAnalyzer()
        self.base_time = datetime.now()
        
        # Sample tweet data
        self.tweet_data = {
            "type": "bullish",
            "coefficient": 0.85,
            "followC": 1000,
            "likeC": 500,
            "viewC": 5000,
            "date": self.base_time,
            "coinType": ["BTC"]
        }
        
        # Sample market data
        self.market_data = {
            "BTC": {
                "current_price": 40000,
                "historical_prices": [
                    40000, 41000, 39500, 40500, 40800,
                    39800, 40200, 41200, 40700, 40000
                ],
                "current_volume": 1000000,
                "average_volume": 800000
            }
        }
    
    def test_combined_analysis(self):
        async def run_test():
            analysis = await self.analyzer.analyze_with_price_predictions(
                self.tweet_data,
                self.market_data
            )
            
            self.assertIn("sentiment_analysis", analysis)
            self.assertIn("price_predictions", analysis)
            self.assertIn("BTC", analysis["price_predictions"])
            
            btc_pred = analysis["price_predictions"]["BTC"]
            self.assertIn("1d", btc_pred)
            self.assertIn("7d", btc_pred)
        
        asyncio.run(run_test())

def run_example_prediction():
    analyzer = EnhancedCryptoAnalyzer()
    
    # Example data
    tweet_data = {
        "type": "bullish",
        "coefficient": 0.9,
        "followC": 5000,
        "likeC": 2000,
        "viewC": 20000,
        "date": datetime.now(),
        "coinType": ["BTC"]
    }
    
    market_data = {
        "BTC": {
            "current_price": 40000,
            "historical_prices": [
                40000, 41000, 39500, 40500, 40800,
                39800, 40200, 41200, 40700, 40000
            ],
            "current_volume": 1200000,
            "average_volume": 800000
        }
    }
    
    async def run_analysis():
        analysis = await analyzer.analyze_with_price_predictions(tweet_data, market_data)
        
        print("\nExample Prediction Results:")
        print("==========================")
        
        print("\nSentiment Analysis:")
        for coin, sentiment in analysis["sentiment_analysis"].items():
            print(f"\n{coin}:")
            print(f"Average Sentiment: {sentiment['average_sentiment']:.3f}")
            print(f"Agreement Ratio: {sentiment['agreement_ratio']:.3f}")
            print("Signal Counts:", sentiment['signal_counts'])
        
        print("\nPrice Predictions:")
        for coin, predictions in analysis["price_predictions"].items():
            print(f"\n{coin}:")
            for timeframe, pred in predictions.items():
                print(f"\n{timeframe} Prediction:")
                print(f"Price Range: ${pred.price_range.min_price:,.2f} - ${pred.price_range.max_price:,.2f}")
                print(f"Confidence: {pred.price_range.confidence * 100:.1f}%")
                print(f"Sentiment Strength: {pred.sentiment_strength:.3f}")
                print(f"Volume Impact: {pred.volume_impact:.3f}")
                print(f"Market Volatility: {pred.market_volatility:.3f}")
    
    asyncio.run(run_analysis())

if __name__ == "__main__":
    unittest.main(verbosity=2, exit=False)
    
    print("\nRunning example prediction...")
    run_example_prediction()