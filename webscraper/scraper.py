from flask import Flask, request, jsonify
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import requests
import time
import json
import re
# from numparser import numparser, text_to_number

# requires:
# selenium
# python-dateutil
# requests


# TODO: session timing out after some time, prevent that, or make it so that it will reboot and pickup where it left off
# SOL, PEPE, BTC, TRUMP, DOGE, SHIBA
coin_tickers = {
    "Solana": "SOL",
    "Pepe": "PEPE",
    "Bitcoin": "BTC",
    "Official Trump": "TRUMP",
    "Dogecoin": "DOGE",
    "Shiba Inu": "SHIB",
}

SESSION_FILE = "session.json"
app = Flask(__name__)

def attach_to_session():
    try:
        with open(SESSION_FILE, "r") as f:
            session_data = json.load(f)

        session_id = session_data["session_id"]
        executor_url = session_data["executor_url"]

        driver = WebDriver(command_executor=executor_url, options=webdriver.ChromeOptions())
        driver.session_id = session_id

        # Test if session is still active
        response = requests.get(f"{executor_url}/session/{session_id}/url")
        if response.status_code != 200:
            print("Session expired. Starting a new session.")
            return start_driver()

        print(f"Reusing existing session: {session_id}")
        return driver

    except (FileNotFoundError, KeyError):
        print("No session found. Starting a new session.")
        return start_driver()
    

def start_driver():
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    driver = webdriver.Remote(
        command_executor="http://localhost:4444/wd/hub",
        options=options
    )

    # Save session ID and command executor URL
    session_data = {"session_id": driver.session_id, "executor_url": "http://localhost:4444/wd/hub"}
    with open(SESSION_FILE, "w") as f:
        json.dump(session_data, f)

    print(f"New session started: {driver.session_id}")
    return driver

def twitter_login(driver, email, username, password):
    driver.get("https://x.com/login")
    time.sleep(5)

    driver.maximize_window()
    time.sleep(3)
    
    email_input = driver.find_element(By.NAME, "text")
    email_input.send_keys(email)
    email_input.send_keys(Keys.RETURN)
    time.sleep(5)
    
    try:
        username_input = driver.find_element(By.NAME, 'text')
        print("found additional login step")

        username_input.send_keys(username)
        username_input.send_keys(Keys.RETURN)
        time.sleep(5)

        password_input = driver.find_element(By.NAME, 'password')
        password_input.send_keys(password)


    except Exception:
        password_input = driver.find_element(By.NAME, 'password')
        print("no such element exception, password page")
        password_input.send_keys(password)

    password_input.send_keys(Keys.RETURN)
    time.sleep(3)
    
    driver.execute_script("document.body.style.zoom = '0.5'")
    time.sleep(3)

    return True

# Searches based on the coin as search query
# Gets top n number of tweets
# Filters tweets using minimum # of likes
def search_twitter(driver, coin, n=10, min_likes=100):
    search_phrase = f'{coin} market min_faves:{min_likes}'

    search_box = driver.find_element(By.XPATH, "//input[@aria-label='Search query']")
    search_box.send_keys(Keys.CONTROL + "a")
    search_box.send_keys(Keys.DELETE)
    search_box.send_keys(search_phrase)
    search_box.send_keys(Keys.RETURN)
    time.sleep(5)
    
    tweets = []
    last_height = driver.execute_script("return document.body.scrollHeight")
    
    while len(tweets) < n:
        new_tweets = driver.find_elements(By.XPATH, "//article[@role='article']")
        for tweet in new_tweets:
            try:
                tweet_text = tweet.find_element(By.XPATH, ".//div[@lang]").text
            except Exception:
                tweet_text = ""
            
            # INORDER: Replies, reposts, likes, bookmarks, views
            stats = tweet.find_element(By.XPATH, ".//div[@role='group']").get_attribute("aria-label").split(", ")

            for stat in stats:
                if "likes" in stat:
                    likes = re.search(r'\d+', stat).group()
                if "views" in stat:
                    views = re.search(r'\d+', stat).group()

            timestamp = tweet.find_element(By.TAG_NAME, "time").get_attribute("datetime")

            # Get follower count
            try:
                # Find the profile icon inside the tweet
                profile_icon = tweet.find_element(By.XPATH, ".//div[contains(@class, 'r-')]//img")

                # Hover over the profile icon
                actions = ActionChains(driver)
                actions.move_to_element(profile_icon).perform()

                time.sleep(2)  # Pause to see the hover effect
                print("Hovered over profile icon")

                # followers_element = driver.find_element(By.XPATH, "//a[contains(@href, 'verified_followers')]")
                followers_element = WebDriverWait(driver, 3).until(
                    EC.presence_of_element_located((By.XPATH, "//a[contains(@href, 'verified_followers')]"))
                )
                followers_text = followers_element.text.split(" ")[0]
                followers = convert_to_number(followers_text)
            except Exception as e:
                print(f"Error hovering over profile icon: {e}")

            tweetobj = {
                "tweet": tweet_text,
                "followC": followers,
                "likeC": likes,
                "viewC": views,
                "date": timestamp,
                "coinType": [coin, coin_tickers[coin]],
            }

            tweets.append(tweetobj)
        
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(3)
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height
    
    return tweets

def search_test(driver, keyword, min_likes=100):
    search_phrase = f'{keyword} min_faves:{min_likes}'

    search_box = driver.find_element(By.XPATH, "//input[@aria-label='Search query']")
    search_box.send_keys(Keys.CONTROL + "a")
    search_box.send_keys(Keys.DELETE)
    search_box.send_keys(search_phrase)
    search_box.send_keys(Keys.RETURN)
    time.sleep(5)

    tweet = driver.find_element(By.XPATH, "//article[@role='article']")
    try:
        # Find the profile icon inside the tweet
        profile_icon = tweet.find_element(By.XPATH, ".//div[contains(@class, 'r-')]//img")

        # Hover over the profile icon
        actions = ActionChains(driver)
        actions.move_to_element(profile_icon).perform()

        time.sleep(2)  # Pause to see the hover effect
        print("Hovered over profile icon")

        followers = driver.find_element(By.XPATH, "//a[contains(@href, 'verified_followers')]").text.split(" ")[0]

        print(convert_to_number(followers))
    except Exception as e:
        print(f"Error hovering over profile icon: {e}")

    return {"msg": "success"}

def convert_to_number(value):
    multipliers = {"K": 1_000, "M": 1_000_000, "B": 1_000_000_000}
    match = re.match(r"([\d\.]+)([KMB]?)", value.strip())  # Extract number and letter

    if match:
        num, suffix = match.groups()
        num = float(num)  # Convert number part to float
        return int(num * multipliers.get(suffix, 1))  # Multiply if suffix exists
    return int(value)  # If no suffix, return as is

@app.route('/login', methods=['GET'])
def login():
    email = request.args.get('email')
    username = request.args.get('username')
    password = request.args.get('password')

    driver = attach_to_session()
    twitter_login(driver, email, username, password)

    return jsonify({"msg": "success"})

@app.route('/search', methods=['GET'])
def search():
    coin = request.args.get('coin')
    n = int(request.args.get('n', 10))  # Default to 10 if not provided
    min_likes = int(request.args.get('min_likes', 100))  # Default to 100 if not provided

    driver = attach_to_session()
    tweets = search_twitter(driver, coin, n, min_likes)
    
    return jsonify(tweets)

@app.route('/searchtest', methods=['GET'])
def searchtest():
    keyword = request.args.get('keyword')
    min_likes = int(request.args.get('min_likes', 100))  # Default to 100 if not provided

    driver = attach_to_session()
    tweets = search_test(driver, keyword, min_likes)
    
    return jsonify(tweets)

if __name__ == "__main__":
    app.run(debug=True, port=8000)