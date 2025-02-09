import unittest
from datetime import datetime, timedelta
from algodev import CryptoSentimentAnalyzer, SentimentConfig

class TestCryptoSentimentAnalyzer(unittest.TestCase):
    def setUp(self):
        """Set up test cases"""
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
        """Test sentiment type mapping"""
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
        """Test engagement metric normalization"""
        test_metrics = [0, 100, 1000, 10000]
        
        for metric in test_metrics:
            normalized = self.analyzer.normalize_engagement_metric(metric)
            self.assertTrue(0 <= normalized <= 1)
            
            if metric <= 0:
                self.assertEqual(normalized, 0)
    
    def test_time_decay(self):
        """Test time decay calculation"""
        test_dates = [
            (self.base_time, 1.0),  # Now
            (self.base_time - timedelta(days=3), 0.74),  # 3 days old
            (self.base_time - timedelta(days=7), 0.50),  # 7 days old
            (self.base_time - timedelta(days=8), 0.0)   # Too old
        ]
        
        for date, expected_decay in test_dates:
            decay = self.analyzer.calculate_time_decay(date)
            self.assertAlmostEqual(decay, expected_decay, places=2)
    
    def test_single_tweet_processing(self):
        """Test processing of a single tweet"""
        result = self.analyzer.process_sentiment_data(self.sample_tweet)
        
        self.assertIn("BTC", result)
        self.assertIn("ETH", result)
        self.assertTrue(result["BTC"] > 0)  # Should be positive for bullish sentiment
    
    def test_multiple_tweets_processing(self):
        """Test processing multiple tweets"""
        tweets = [
            # Bullish BTC tweet
            {
                "type": "bullish",
                "coefficient": 0.9,
                "followC": 1000,
                "likeC": 500,
                "viewC": 5000,
                "date": self.base_time,
                "coinType": ["BTC"]
            },
            # Bearish BTC tweet
            {
                "type": "bearish",
                "coefficient": 0.8,
                "followC": 800,
                "likeC": 400,
                "viewC": 4000,
                "date": self.base_time,
                "coinType": ["BTC"]
            },
            # Neutral ETH tweet
            {
                "type": "neutral",
                "coefficient": 0.7,
                "followC": 600,
                "likeC": 300,
                "viewC": 3000,
                "date": self.base_time,
                "coinType": ["ETH"]
            }
        ]
        
        for tweet in tweets:
            self.analyzer.process_sentiment_data(tweet)
        
        analysis = self.analyzer.get_coin_analysis()
        
        self.assertIn("BTC", analysis)
        self.assertIn("ETH", analysis)
        self.assertEqual(analysis["BTC"]["signal_counts"]["total"], 2)
        self.assertEqual(analysis["ETH"]["signal_counts"]["total"], 1)
    
    def test_trend_strength(self):
        """Test trend strength calculation"""
        signals = [
            {"score": 0.5, "timestamp": self.base_time - timedelta(days=6)},
            {"score": 0.6, "timestamp": self.base_time - timedelta(days=4)},
            {"score": 0.7, "timestamp": self.base_time - timedelta(days=2)},
            {"score": 0.8, "timestamp": self.base_time}
        ]
        
        trend_strength = self.analyzer.calculate_trend_strength(signals)
        self.assertTrue(trend_strength > 0)  # Should be positive for increasing trend
    
    def test_custom_config(self):
        """Test analyzer with custom configuration"""
        custom_config = SentimentConfig(
            SENTIMENT_WEIGHT=0.7,
            ENGAGEMENT_WEIGHT=0.3,
            TIME_DECAY_ALPHA=0.2
        )
        
        custom_analyzer = CryptoSentimentAnalyzer(config=custom_config)
        result = custom_analyzer.process_sentiment_data(self.sample_tweet)
        
        self.assertIn("BTC", result)
        self.assertNotEqual(result["BTC"], 
                          self.analyzer.process_sentiment_data(self.sample_tweet)["BTC"])
    
    def test_reset_aggregator(self):
        """Test aggregator reset functionality"""
        self.analyzer.process_sentiment_data(self.sample_tweet)
        self.assertTrue(len(self.analyzer.aggregator) > 0)
        
        self.analyzer.reset_aggregator()
        self.assertEqual(len(self.analyzer.aggregator), 0)
    
    def test_edge_cases(self):
        """Test edge cases and error handling"""
        edge_cases = [
            # Zero engagement
            {
                "type": "bullish",
                "coefficient": 0.9,
                "followC": 0,
                "likeC": 0,
                "viewC": 0,
                "date": self.base_time,
                "coinType": ["BTC"]
            },
            # Very high engagement
            {
                "type": "bullish",
                "coefficient": 0.9,
                "followC": 1000000,
                "likeC": 500000,
                "viewC": 5000000,
                "date": self.base_time,
                "coinType": ["BTC"]
            },
            # Invalid sentiment type
            {
                "type": "invalid",
                "coefficient": 0.9,
                "followC": 1000,
                "likeC": 500,
                "viewC": 5000,
                "date": self.base_time,
                "coinType": ["BTC"]
            }
        ]
        
        for case in edge_cases:
            result = self.analyzer.process_sentiment_data(case)
            self.assertIsInstance(result, dict)

def generate_sample_data():
    """Generate sample data for manual testing"""
    base_time = datetime.now()
    sample_data = []
    
    # Generate tweets over the past week
    for days_ago in range(7):
        for _ in range(5):  # 5 tweets per day
            sample_data.append({
                "type": "bullish" if days_ago % 2 == 0 else "bearish",
                "coefficient": 0.7 + (days_ago % 3) * 0.1,
                "followC": 1000 + days_ago * 100,
                "likeC": 500 + days_ago * 50,
                "viewC": 5000 + days_ago * 500,
                "date": base_time - timedelta(days=days_ago),
                "coinType": ["BTC", "ETH"] if days_ago % 2 == 0 else ["BTC"]
            })
    
    return sample_data

if __name__ == "__main__":
    # Run unit tests
    print("Running unit tests...")
    unittest.main(verbosity=2, exit=False)
    
    # Manual testing with sample data
    print("\nRunning manual test with sample data...")
    analyzer = CryptoSentimentAnalyzer()
    sample_data = generate_sample_data()
    
    for tweet in sample_data:
        analyzer.process_sentiment_data(tweet)
    
    analysis = analyzer.get_coin_analysis()
    
    print("\nFinal Analysis:")
    for coin, metrics in analysis.items():
        print(f"\n{coin} Analysis:")
        print(f"Average Sentiment: {metrics['average_sentiment']:.3f}")
        print(f"Sentiment Volume: {metrics['sentiment_volume']:.3f}")
        print(f"Trend Strength: {metrics['trend_strength']:.3f}")
        print(f"Agreement Ratio: {metrics['agreement_ratio']:.3f}")
        print("Signal Counts:", metrics['signal_counts'])
        print("Recommendation:", metrics['recommendation'])