from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import time
import random
import sys

from imap_tools import MailBox,AND

from loguru import logger
logger.configure(handlers=[{  
    "sink": sys.stdout,  
    "format": "<yellow>{time:YYYY-MM-DD HH:mm:ss}</yellow> | "  
            "<level>{level}</level> | "  
            "<cyan>{module}</cyan>:<cyan>{function}</cyan> | "  
            "<yellow>{message}</yellow>",  
    "colorize": True   
}])  

usernames=["Kellymartin2508"]
emails=["projecttest.tech@gmail.com"]
passwords=["P@ssw0rd123123"]

email_user="projecttest.tech@gmail.com"
email_pass="P@ssw0rd123123"
import jmespath
import sys
from typing import Dict

from playwright.sync_api import sync_playwright

from loguru import logger
logger.configure(handlers=[{  
    "sink": sys.stdout,  
    "format": "<yellow>{time:YYYY-MM-DD HH:mm:ss}</yellow> | "  
            "<level>{level}</level> | "  
            "<cyan>{module}</cyan>:<cyan>{function}</cyan> | "  
            "<yellow>{message}</yellow>",  
    "colorize": True   
}])  

def is_twitter_url(url):
    twitter_domains = ["twitter.com", "https://x.com", "https://t.co"]  
    for domain in twitter_domains:  
        if domain in url:  
            return True  
    return False  

def check_latest_email():
    with MailBox("imap.gmail.com").login(email_user,email_pass,'INBOX') as mailbox:
        logger.info("1")
        emails=list(mailbox.fetch(AND(seen=False),limit=1,reverse=True))
        logger.info("2")

        if len(emails)==0:
            return None,None,None
        
        logger.info("3")
        return emails[0]
    
def x_sign_in(driver):
    driver.get("https://twitter.com/i/flow/login")
    
    #time.sleep(random.uniform(5,9))
    time.sleep(9)
    email_input_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.NAME, "text"))
        )

    # Send text to the input field
    email_input_field.send_keys(random.choice(emails))
    logger.info("Text sent successfully.")
    element = WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.XPATH, "//*[text()='Next']"))
        )
    element.click()
    time.sleep(5)
    driver.save_screenshot("screenshot/screenshot1.png")

    try:
        name_input_field = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.NAME, "text"))
            )
        
        if name_input_field:
                # Send text to the input field
            name_input_field.send_keys(random.choice(usernames))
            logger.info("Text sent successfully.")
            element = WebDriverWait(driver, 10).until(
                    EC.visibility_of_element_located((By.XPATH, "//*[text()='Next']"))
                )
            element.click()
    except:
        logger.error("No name needed")
    time.sleep(5)
    driver.save_screenshot("screenshot/screenshot2.png")

    password_input_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.NAME, "password"))
        )

        # Send text to the input field
    password_input_field.send_keys(random.choice(passwords))
    logger.info("password sent successfully.")
    time.sleep(5)
    driver.save_screenshot("screenshot/screenshot3.png")

    element = WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.XPATH, "//*[text()='Log in']"))
        )
    element.click()
    time.sleep(5)
    driver.save_screenshot("screenshot/screenshot4.png")

    try:
        element = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.NAME, "text"))
            )
        if element:
            time.sleep(2)
            neat=check_latest_email().subject.split(' ')[-1]
            # neat = "simr66n6"
            element.send_keys(neat)

            nxt = WebDriverWait(driver, 10).until(
                EC.visibility_of_element_located((By.XPATH, "//*[text()='Next']"))
            )
            nxt.click()
            logger.info(neat)
    except:
        logger.info("No confirmation")
    time.sleep(10)
    driver.save_screenshot("screenshot/screenshot5.png")


def scrape_tweet(url: str) -> dict:
    """
    Scrape a single tweet page for Tweet thread e.g.:
    https://twitter.com/Scrapfly_dev/status/1667013143904567296
    Return parent tweet, reply tweets and recommended tweets
    """
    _xhr_calls = []

    def intercept_response(response):
        """capture all background requests and save them"""
        # we can extract details from background requests
        if response.request.resource_type == "xhr":
            _xhr_calls.append(response)
        return response

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1920, "height": 1080})
        page = context.new_page()

        # enable background request intercepting:
        page.on("response", intercept_response)
        # go to url and wait for the page to load
        page.goto(url)
        page.wait_for_selector("//*[@data-testid='tweet']")

        # find all tweet background requests:
        tweet_calls = [f for f in _xhr_calls if "TweetResultByRestId" in f.url]
        for xhr in tweet_calls:
            data = xhr.json()
            return data['data']['tweetResult']['result']

def parse_tweet(url: str) -> Dict: 
    logger.info("We are running parse_tweet function!")  

    max_retries = 3  # Maximum retries  
    attempts = 0  

    while attempts < max_retries:  
        try:  
            # Increment the attempt counter  
            attempts += 1  
            
            # Attempt to scrape and parse the tweet  
            data = scrape_tweet(url)  

            """Parse Twitter tweet JSON dataset for the most important fields"""  
            result = jmespath.search(  
                """{  
                created_at: legacy.created_at,  
                attached_urls: legacy.entities.urls[].expanded_url,  
                attached_urls2: legacy.entities.url.urls[].expanded_url,  
                attached_media: legacy.entities.media[].media_url_https,  
                tagged_users: legacy.entities.user_mentions[].screen_name,  
                tagged_hashtags: legacy.entities.hashtags[].text,  
                favorite_count: legacy.favorite_count,  
                bookmark_count: legacy.bookmark_count,  
                quote_count: legacy.quote_count,  
                reply_count: legacy.reply_count,  
                retweet_count: legacy.retweet_count,  
                quote_count: legacy.quote_count,  
                text: legacy.full_text,  
                is_quote: legacy.is_quote_status,  
                is_retweet: legacy.retweeted,  
                language: legacy.lang,  
                user_id: legacy.user_id_str,  
                id: legacy.id_str,  
                conversation_id: legacy.conversation_id_str,  
                source: source,  
                views: views.count  
            }""",  
                data,  
            )  
            
            # Parse poll data  
            result["poll"] = {}  
            poll_data = jmespath.search("card.legacy.binding_values", data) or []  
            for poll_entry in poll_data:  
                key, value = poll_entry["key"], poll_entry["value"]  
                if "choice" in key:  
                    result["poll"][key] = value["string_value"]  
                elif "end_datetime" in key:  
                    result["poll"]["end"] = value["string_value"]  
                elif "last_updated_datetime" in key:  
                    result["poll"]["updated"] = value["string_value"]  
                elif "counts_are_final" in key:  
                    result["poll"]["ended"] = value["boolean_value"]  
                elif "duration_minutes" in key:  
                    result["poll"]["duration"] = value["string_value"]  

            # Fallback if attached_media is empty  
            if not result["attached_media"]:  
                result["attached_media"] = [""]  

            # Logging success  
            logger.info(f"Tweet parsed successfully on attempt {attempts}")  
            
            # Return parsed data  
            return result["created_at"], result["text"], result["attached_media"][0]  

        except Exception as e:  
            # Log the error  
            logger.error(f"Error occurred while parsing tweet on attempt {attempts}: {e}")  

            # If max retries have been reached, log and return None  
            if attempts == max_retries:  
                logger.error("Max retries reached. Failed to parse tweet.")  
                return "", "", ""

def scrape_profile(url: str) -> dict:
    """
    Scrape a X.com profile details e.g.: https://x.com/Scrapfly_dev
    """
    _xhr_calls = []

    def intercept_response(response):
        """capture all background requests and save them"""
        # we can extract details from background requests
        if response.request.resource_type == "xhr":
            _xhr_calls.append(response)
        return response

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1920, "height": 1080})
        page = context.new_page()

        # enable background request intercepting:
        page.on("response", intercept_response)
        # go to url and wait for the page to load
        page.goto(url)
        page.wait_for_selector("[data-testid='primaryColumn']")

        # find all tweet background requests:
        tweet_calls = [f for f in _xhr_calls if "UserBy" in f.url]
        for xhr in tweet_calls:
            data = xhr.json()
            return data['data']['user']['result']
