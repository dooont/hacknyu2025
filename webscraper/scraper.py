from getpass import getpass
from time import sleep
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver import Chrome, ChromeOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

driver = Chrome()
sleeptime = 3

email_addr = 'evan321lin@gmail.com'
user = 'evanlin1278484'
passw = 'test123test'

driver.get("https://x.com/login")
sleep(5)

# Maximize window
driver.maximize_window()
sleep(sleeptime)

# Enter username
email = driver.find_element(By.NAME, 'text')

email.send_keys(email_addr)
email.send_keys(Keys.RETURN)

sleep(sleeptime)
try:
    username = driver.find_element(By.NAME, 'text')
    print("found additional login step")

    username.send_keys(user)
    username.send_keys(Keys.RETURN)
    sleep(sleeptime)

    password = driver.find_element(By.NAME, 'password')
    password.send_keys(passw)

except NoSuchElementException:
    password = driver.find_element(By.NAME, 'password')
    print("no such element exception, password page")
    password.send_keys(passw)

password.send_keys(Keys.RETURN)
sleep(sleeptime)
print("logged in")

def search_twitter(driver, keyword, n_tweets=10):
    search_box = driver.find_element(By.XPATH, "//input[@aria-label='Search query']")
    search_box.send_keys(keyword)
    search_box.send_keys(Keys.RETURN)
    sleep(5)
    
    tweets = set()
    last_height = driver.execute_script("return document.body.scrollHeight")

    resultsfile = open("results.txt", "w")
    
    while len(tweets) < n_tweets:
        tweet_elements = driver.find_elements(By.XPATH, "//div[@data-testid='tweetText']")
        for tweet in tweet_elements:
            tweets.add(tweet.text)
            if len(tweets) >= n_tweets:
                break
        
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        sleep(3)
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height
    
    for tweet in list(tweets)[:n_tweets]:
        print(tweet)
        print("-----------------------------------")
        resultsfile.write(tweet + "\n")
        resultsfile.write("-----------------------------------\n")

search_twitter(driver, "solana")
print("search successful")

sleep(10)
resp = driver.page_source