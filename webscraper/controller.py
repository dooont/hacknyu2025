from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import time

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
    search_box.send_keys(search_phrase)
    search_box.send_keys(Keys.RETURN)
    time.sleep(5)
    
    tweets = set()
    last_height = driver.execute_script("return document.body.scrollHeight")
    
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

if __name__ == "__main__":
    # search_twitter()
    driver = webdriver.Remote(
        command_executor="http://localhost:4444/wd/hub",
        options=webdriver.ChromeOptions()
    )

    # twitter_login(driver, "evan321lin@gmail.com", "evanlin1278484", "test123test")
    search_twitter(driver, "solana market", 3, 100)
