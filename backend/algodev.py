import json
from datetime import datetime
import math


# ----------------------------------------------------
#  Global Aggregator:
#    aggregator[coin_symbol] = {
#      "bullish_total": 0.0,
#      "bearish_total": 0.0,
#      "neutral_count": 0
#    }
# ----------------------------------------------------
aggregator = {}  # We’ll update this for each coin


def collect_data_from_json(json_string):
    """
    Parses the JSON string and extracts relevant fields.
    """
    data = json.loads(json_string)
    
    # Convert the date string to a datetime object (if possible)
    try:
        date_obj = datetime.fromisoformat(data["date"].replace("Z", ""))
    except (ValueError, KeyError):
        # Fallback if date parsing fails or date key missing
        date_obj = datetime.now()
    
    return {
        "type": data.get("type", "neutral"),
        "coefficient": float(data.get("coefficient", 0.0)),
        "followC": int(data.get("followC", 0)),
        "likeC": int(data.get("likeC", 0)),
        "viewC": int(data.get("viewC", 1)),  # avoid zero division
        "date": date_obj,
        "coinType": data.get("coinType", [])
    }


def process_sentiment_data(coin_data, alpha=0.1):
    """
    Computes a sentiment-based percentage (the old "potential price change").
    Then updates our global aggregator with bullish, bearish, or neutral data.
    """
    # 1. Determine sentiment factor (+1 for bullish, -1 for bearish, 0 for neutral)
    sentiment_type = coin_data["type"].lower()
    if sentiment_type == "bullish":
        sentiment_factor = 1
    elif sentiment_type == "bearish":
        sentiment_factor = -1
    else:
        sentiment_factor = 0

    # 2. Engagement ratio
    follow_count = coin_data["followC"]
    like_count   = coin_data["likeC"]
    view_count   = coin_data["viewC"]
    engagement_ratio = (follow_count + like_count) / float(view_count)

    # 3. Base score
    base_score = sentiment_factor * coin_data["coefficient"]

    # 4. Time decay factor
    now = datetime.now()
    time_diff_days = (now - coin_data["date"]).total_seconds() / 86400.0
    time_factor = math.exp(-alpha * time_diff_days)

    # 5. Calculate final score -> potential price change in percentage
    final_score = base_score * engagement_ratio * time_factor
    potential_price_change_percent = final_score * 100

    # 6. Update aggregator for each coin symbol in coin_data["coinType"]
    for coin_symbol in coin_data["coinType"]:
        # Make sure the aggregator has an entry for this coin
        if coin_symbol not in aggregator:
            aggregator[coin_symbol] = {
                "bullish_total": 0.0,
                "bearish_total": 0.0,
                "neutral_count": 0
            }
        
        if sentiment_factor > 0:   # bullish
            aggregator[coin_symbol]["bullish_total"] += potential_price_change_percent
        elif sentiment_factor < 0: # bearish
            aggregator[coin_symbol]["bearish_total"] += potential_price_change_percent
        else:                      # neutral
            aggregator[coin_symbol]["neutral_count"] += 1


def calculate_final_change_for_coins():
    """
    For each coin in aggregator, calculate:
      overall_percentage_change = bullish_total - bearish_total
      final_change = (overall_percentage_change * 100) / neutral_count
    and return or print the results.
    """
    results = {}
    for coin_symbol, data in aggregator.items():
        bullish_total = data["bullish_total"]
        bearish_total = data["bearish_total"]
        neutral_count = data["neutral_count"]

        overall_percentage_change = bullish_total - bearish_total
        
        # Avoid dividing by zero
        if neutral_count > 0:
            final_change = (overall_percentage_change * 100) / neutral_count
        else:
            final_change = 0.0  # or some fallback if no neutrals

        results[coin_symbol] = {
            "overall_percentage_change": overall_percentage_change,
            "neutral_count": neutral_count,
            "final_change": final_change
        }
    return results


def run_tests_on_json_file(json_file_path, alpha=0.1):
    """
    Reads a JSON file containing an array of items,
    calls process_sentiment_data on each,
    then calculates final changes for all coins.
    """
    with open(json_file_path, 'r') as f:
        data_list = json.load(f)
    
    if not isinstance(data_list, list):
        raise ValueError("Expected the JSON file to contain a list of items.")

    # Process each item
    for i, item in enumerate(data_list, start=1):
        item_json = json.dumps(item)  # turn item back into a JSON string
        coin_data = collect_data_from_json(item_json)
        process_sentiment_data(coin_data, alpha=alpha)

    # Now compute final changes
    results = calculate_final_change_for_coins()

    # Print results
    print("\n======== Final Results Per Coin ========")
    for coin_symbol, result_data in results.items():
        print(f"Coin: {coin_symbol}")
        print(f"  Overall % Change (Bullish - Bearish): {result_data['overall_percentage_change']:.2f}")
        print(f"  Neutral Count: {result_data['neutral_count']}")
        print(f"  Final Change: {result_data['final_change']:.2f}\n")


if __name__ == "__main__":
    # Example usage: pass in a sample JSON file with multiple entries
    sample_file_path = "sample_crypto_data.json"
    run_tests_on_json_file(sample_file_path, alpha=0.1)
