from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webdriver import WebDriver
import requests
import time
import json

SESSION_FILE = "session.json"


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

def search_twitter(driver, keyword, n=10, min_likes=100):
    search_phrase = f'{keyword} min_faves:{min_likes}'

    search_box = driver.find_element(By.XPATH, "//input[@aria-label='Search query']")
    search_box.send_keys(Keys.CONTROL + "a")
    search_box.send_keys(Keys.DELETE)
    search_box.send_keys(search_phrase)
    search_box.send_keys(Keys.RETURN)
    time.sleep(5)
    
    tweets = set()
    last_height = driver.execute_script("return document.body.scrollHeight")

    resultsfile = open("results.txt", "w", encoding="utf-8")
    
    while len(tweets) < n:
        new_tweets = driver.find_elements(By.XPATH, "//div[@data-testid='tweetText']")
        for tweet in new_tweets:
            tweets.add(tweet.text)
            if len(tweets) >= n:
                break
        
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(3)
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height
    
    for tweet in list(tweets)[:n]:
        print(tweet)
        print("-----------------------------------")
        res = f'{tweet}\n'
        resultsfile.write(res)
        resultsfile.write("-----------------------------------\n")

if __name__ == "__main__":
    driver = attach_to_session()
    
    print("Selenium browser is running. You can interact with it using the driver instance.")

    # twitter_login(driver, "evan321lin@gmail.com", "evanlin1278484", "test123test")
    search_twitter(driver, "solana market", 3)
