# test.py
# import default libraries
import time  
import sys
import json  
import re
import os
import random
import requests

# import environment libraries
from dotenv import load_dotenv
load_dotenv()

# import selenium related libraries
from selenium import webdriver  
from seleniumwire import webdriver
from selenium.webdriver.chrome.service import Service  
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# import funtions from other files
from db import initialize_firestore, insert_article, check_if_exists
from serper import get_article_info_from_serper
from parse_utils import (  
    clean_article_url,  
    get_domain_from_url,
    parse_html,  
    parse_twitter_html,
    parse_post_date,  
    calculate_days_behind,
)
from exception_case import get_more_articles
from twitter import x_sign_in, is_twitter_url, parse_tweet, resolve_tco_url

# import logging libraries
from loguru import logger
logger.configure(handlers=[{  
    "sink": sys.stdout,  
    "format": "<yellow>{time:YYYY-MM-DD HH:mm:ss}</yellow> | "  
            "<level>{level}</level> | "  
            "<cyan>{module}</cyan>:<cyan>{function}</cyan> | "  
            "<yellow>{message}</yellow>",  
    "colorize": True   
}])  

class Generalscrapper():
    def __init__(self):
        self.cloudflare_exceptions = ["mahanow.org", "tuckercarlson.com"]
        self.view_exceptions = ["theamericanconservative.com", "nopharmfilm.com"]
        self.SCRAPEOPS_API_KEY = os.getenv("SCRAPEOPS_API_KEY")

        # initialize firebase
        self.db_general = initialize_firestore("Firebase_Credentials_General_Platform", app_name="General_Platform")
        self.db_video = initialize_firestore("Firebase_Credentials_Video_Platform", app_name="Video_Platform")
        self.db_x = initialize_firestore("Firebase_Credentials_X_Platform", app_name="X_Platform")

    def setup_driver(self, url):
        # Handle Cloudflare url
        if get_domain_from_url(url) in self.cloudflare_exceptions:
            logger.info("Cloudflare protected")
            options = webdriver.ChromeOptions()
            user_agents = [
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.150 Safari/537.36",
            ]
            user_agent = random.choice(user_agents)
            options.add_argument(f"user-agent={user_agent}")
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_argument("--blink-settings=imagesEnabled=false")
            # options.add_argument("--headless")
            
            # set up proxy
            proxy_options = {
                "proxy": {
                    "http": f"http://scrapeops.headless_browser_mode=true:{self.SCRAPEOPS_API_KEY}@proxy.scrapeops.io:5353",
                    "https": f"http://scrapeops.headless_browser_mode=true:{self.SCRAPEOPS_API_KEY}@proxy.scrapeops.io:5353",
                    "no_proxy": "localhost:127.0.0.1",
                }
            }
            driver = webdriver.Chrome(options=options, seleniumwire_options=proxy_options)
            return driver

        # Handle ordinal url    
        chrome_options = webdriver.ChromeOptions()   
        chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.150 Safari/537.36')  
        chrome_options.add_argument('--disable-popup-blocking')  # Disable popup blocks  
        chrome_options.add_argument('--disable-background-timer-throttling')  # Disable background throttling  
        chrome_options.add_argument('--disable-infobars')  # Disable info bars in the UI (e.g., "Chrome is being controlled...")  
        chrome_options.add_argument('--ignore-gpu-blacklist')  # Force enabling GPU even if unsupported by default  
        chrome_options.add_argument('--no-sandbox')  # Bypass OS security model (needed in some environments)  
        chrome_options.add_argument('--disable-dev-shm-usage')  # Prevent crashes due to limited /dev/shm  
        chrome_options.add_argument('--disable-gpu')  # Disable GPU (needed for some rendering issues in headless mode)  
        chrome_options.add_argument('--window-size=1920,1080')  # Set browser window size (needed for responsive web pages)  
        chrome_options.add_argument('--start-maximized')  # Ensure full content is visible  
        chrome_options.add_argument('--disable-extensions')  # Disable extensions for stability  
        chrome_options.add_argument('--headless')  # Run in headless mode (no browser window) 
        
        webdriver_service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=webdriver_service, options = chrome_options)
        return driver

    def get_one_tweet_data(self, element, article_domain):
        tweet_data = []
        post_html = element.get_attribute("outerHTML")  
        tweet_data = parse_twitter_html(post_html)

        if tweet_data["article_url"] and tweet_data["article_title"]:
            # Clean title of article
            sanitized_title = re.sub(r'[/*~[\]<>.]', '', tweet_data["article_title"])  
            sanitized_title = sanitized_title.strip() 
            tweet_data["article_title"] = sanitized_title

            tweet_data["article_url"], tweet_data["article_image_url"] = clean_article_url(tweet_data["article_url"], tweet_data["article_image_url"], article_domain)
        else:
            tweet_data = []

        if tweet_data == []:  
            with open("log.txt", "a") as f:  
                f.write("Failed post html\n")  
                f.write(post_html + "\n")  # Assuming `post_html` is a string variable

        return tweet_data
    
    def get_one_article_data(self, element, article_domain):
        article_data = []
        upper_trying_count = 0
        while True:
            # If we've tried 5 times to go to the upper level, break the loop
            if upper_trying_count == 5:
                logger.info("Tried 5 times to upper level. But couldn't find actual article")
                break            
            
            # Get the outer HTML of the element and parsing it.
            try:            
                post_html = element.get_attribute("outerHTML")  
            except Exception as e:
                post_html = ""            
            article_data = parse_html(post_html)
            if article_data["article_url"] and article_data["article_title"]:
                # Clean title of article that could be the document of firebase
                sanitized_title = re.sub(r'[/*~[\]<>.]', '', article_data["article_title"])  
                sanitized_title = sanitized_title.strip() 
                article_data["article_title"] = sanitized_title

                # Clean article url and article_image_url
                article_data["article_url"], article_data["article_image_url"] = clean_article_url(article_data["article_url"], article_data["article_image_url"], article_domain)
                break
            else:
                article_data = []
                try: 
                    element = element.find_element(By.XPATH, './..') 
                except Exception as e:
                    logger.info(f"Couldn't find any parent element: {e}")
                    break
                logger.info(f"\nDidn't found, dive deep one level more- {upper_trying_count}\n")
                upper_trying_count += 1
                continue
        
        return article_data
    
    def get_tweet_data_from_one_page(self, driver, db, url, parse_type, days_behind):
        logger.info(f"\033[31m We are handling new X url. Current url: {url}\033[0m")

        self.page_consider = 0
        article_domain = get_domain_from_url(url)
        username = url.split('/')[-1] if url.startswith("https://x.com/") else "" 
        if username == "": 
            username = url.split('/')[-1] if url.startswith("https://twitter.com/") else None  

        time.sleep(10)
        WebDriverWait(driver, 20).until(lambda d: d.execute_script("return document.readyState") == "complete")   
        elements = driver.find_elements(By.XPATH, parse_type)  

        if elements:  
            logger.info(f"len(elements): {len(elements)}")  
            for element in elements:
                try:         
                    if self.consider_exit == 50:
                        logger.info("Exiting loop after 50 empty elements")
                        self.page_consider = 0
                        break
                    
                    attempt = 0  # Initialize attempt counter  
                    while attempt < 3:  # Try extracting the tweet data up to 3 times  
                        try:
                            tweet_data = self.get_one_tweet_data(element, article_domain) 
                        except Exception as e:
                            tweet_data = [] 
                        if tweet_data != []:  # If successful, exit the retry loop  
                            break  
                        attempt += 1  # Increment the attempt counter if no success  
                        logger.info(f"Couldn't find actual tweet from the element. Attempt: {attempt}")
                    
                    if attempt == 3:  # If all 3 attempts fail, handle failure  
                        self.consider_exit += 1  
                        logger.error("Couldn't find actual tweet from the element after 3 attempts")  
                        continue  # Skip to the next element  
                                    
                    if tweet_data["article_url"].startswith("https://t.co/") or tweet_data["article_url"].startswith("http://t.co/"):  
                        logger.info("\033[94mFound t.co url, attempting to change to profile URL - {}\033[0m", tweet_data   ["article_url"])  
                        tweet_data["article_url"] = resolve_tco_url(tweet_data["article_url"])

                    if tweet_data["article_url"] and tweet_data["article_title"]:
                        if check_if_exists(db, username, tweet_data["article_title"]):
                            self.consider_exit += 1
                            continue

                        temp_age = tweet_data["article_age"]
                        if is_twitter_url(tweet_data["article_url"]):                        
                            tweet_data["article_age"], tweet_data["text"], temp_image_url = parse_tweet(tweet_data["article_url"])
                        else:
                            logger.info("Not a twitter url. Parsing with serper")
                            try:
                                tweet_data["article_age"], tweet_data["text"] = get_article_info_from_serper(tweet_data["article_url"])
                                temp_image_url = ""
                            except Exception as e:
                                tweet_data["article_age"], tweet_data["text"] = "", ""
                                logger.info(f"Error getting article info from serper: {e}")
                                
                        if tweet_data["article_age"] == "":
                            logger.info(f"Failed to get article age using tweet parge function. Trying to get article age using post date - {temp_age}")
                            try:    
                                tweet_data["article_age"] = parse_post_date(temp_age)
                            except Exception as e:
                                tweet_data["article_age"] = ""
                                logger.info(f"Error getting article age from post date: {e}")
                            
                            if calculate_days_behind(tweet_data["article_age"]) > days_behind:
                                self.consider_exit += 1
                                logger.info(f"\033[91mArticle is older than {days_behind} days. Skipping\033[0m")  
                                continue
                                
                        if tweet_data["article_image_url"] == "":
                            tweet_data["article_image_url"] = temp_image_url
                            
                        insert_article(db, username, tweet_data)               
                        self.page_consider += 1
                except Exception as e:
                    logger.error(f"Error in get_tweet_data_from_one_page: {e}")
        
        return self.page_consider
                
    def get_article_data_from_one_page(self, driver, db, url, view_type, parse_type, days_behind): 
        logger.info(f"\033[31m We are handling new url in same domain. Current url: {url}\033[0m")
        self.page_consider = 0
        article_domain = get_domain_from_url(url)
        
        self.exception_list = ["scroll", "exception"]
        if view_type not in self.exception_list:
            driver.get(url)  
            
        logger.info(f"Current URL - {url}")
        logger.info(f"Our main domain is - {article_domain}")

        time.sleep(10)
        WebDriverWait(driver, 20).until(lambda d: d.execute_script("return document.readyState") == "complete")  

        elements = driver.find_elements(By.XPATH, parse_type)  
        if elements:  
            logger.info(f"len(elements): {len(elements)}")  
            for element in elements: 
                try:        
                    if self.consider_exit == 50:
                        logger.info("Exiting loop after 50 empty elements")
                        self.page_consider = 0
                        break
                        
                    attempt = 0  # Initialize attempt counter  
                    while attempt < 3:  # Try extracting the article data up to 3 times  
                        article_data = self.get_one_article_data(element, article_domain)  
                        if article_data != []:  # If successful, exit the retry loop  
                            break  
                        attempt += 1  # Increment the attempt counter if no success  
                        logger.info(f"Couldn't find actual article from the element. Attempt: {attempt}")
                    
                    if attempt == 3:  # If all 3 attempts fail, handle failure  
                        self.consider_exit += 1  
                        logger.error("Couldn't find actual article from the element after 3 attempts")  
                        continue  # Skip to the next element  
                                    
                    if article_data == []:
                        self.consider_exit += 1
                        logger.info("Couldn't find actual article from the element")                    
                        continue

                    if article_data["article_url"] and article_data["article_title"]:
                        if article_domain == "freevoicemedianewsletter.beehiiv.com":
                            article_data["article_title"] = article_data["article_title"] + " " + article_data["article_age"]
                        if check_if_exists(db, article_domain, article_data["article_title"]):
                            self.consider_exit += 1
                            continue

                        temp_age = article_data["article_age"]
                        try:
                            article_data["text"], article_data["article_age"] = get_article_info_from_serper(article_data["article_url"])
                        except Exception as e:
                            article_data["text"], article_data["article_age"] = "", ""
                            logger.info(f"Error getting article info from serper: {e}")

                        if article_data["article_age"] == "":
                            logger.info(f"Failed to get article age using serper. Trying to get article age using post date - {temp_age}")
                            try:
                                article_data["article_age"] = parse_post_date(temp_age)
                            except Exception as e:
                                article_data["article_age"] = ""
                                logger.info(f"Error getting article age from post date: {e}")
                            
                        if article_data["article_age"] != "":
                            if calculate_days_behind(article_data["article_age"]) > days_behind:
                                self.consider_exit += 1
                                logger.info(f"Article is older than {days_behind} days. Skipping\n")
                                continue
                        
                        insert_article(db, article_domain, article_data)               
                        self.page_consider += 1
                except Exception as e:
                    logger.error(f"Error in get_article_data_from_one_page: {e}") 
             
        return self.page_consider

    def get_whole_article_data(self, driver, db, url, view_type, parse_type, days_behind):
        base_url = url
        page_num = 1
        if view_type == "page1":
            if get_domain_from_url(url) == "thelibertydaily.com":
                logger.info(f"We met a special case - {url}")
                page_num = 5
                url = f"{base_url}/page/{page_num}/"
            while True:
                self.page_consider = self.get_article_data_from_one_page(driver, db, url, view_type, parse_type, days_behind)
                if self.page_consider == 0:
                    logger.info(f"We can't find any new article in page {page_num}. Stop searching and choice is set as page1\n")
                    break
                page_num += 1
                url = f"{base_url}/page/{page_num}/"
            
        if view_type == "page2":
            if get_domain_from_url(url) == "actforamerica.org":
                page_num = 0
            while True:
                self.page_consider = self.get_article_data_from_one_page(driver, db, url, view_type, parse_type, days_behind)
                if self.page_consider == 0:
                    logger.info(f"We can't find any new article in page {page_num}. Stop searching and choice is set as page2\n")
                    break
                page_num += 1
                url = f"{base_url}?page={page_num}"
        
        if view_type == "page3":
            while True:
                self.page_consider = self.get_article_data_from_one_page(driver, db, url, view_type, parse_type, days_behind)
                if self.page_consider == 0:
                    logger.info(f"We can't find any new article in page {page_num}. Stop searching and choice is set as page2\n")
                    break
                page_num += 1
                url = f"{base_url}?page_number={page_num}#news-archive"
        
        if view_type == "page4":
            while True:
                self.page_consider = self.get_article_data_from_one_page(driver, db, url, view_type, parse_type, days_behind)
                if self.page_consider == 0:
                    logger.info(f"We can't find any new article in page {page_num}. Stop searching and choice is set as page4\n")
                    break
                page_num += 1
                url = f"{base_url}?pg={page_num}"
             
        if view_type == "scroll":
            if get_domain_from_url(url) == "podcasts.apple.com":
                driver.get(url)
                get_more_articles(driver, get_domain_from_url(url))
            
            last_height = driver.execute_script("return document.body.scrollHeight")  
            url = base_url
            driver.get(url)
            while True:    
                time.sleep(10)

                if get_domain_from_url(url) == "x.com" or get_domain_from_url(url) == "twitter.com":
                    logger.info("We are running get_tweet_data_from_one_page function")
                    self.page_consider = self.get_tweet_data_from_one_page(driver, db, url, parse_type, days_behind)  
                else:
                    self.page_consider = self.get_article_data_from_one_page(driver, db, url, view_type, parse_type, days_behind)  

                if self.page_consider == 0:
                    logger.info(f"We can't find any new article in page {page_num}. Stop searching and choice is set as scroll\n")
                    break
                
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")  
                time.sleep(10)  
                new_height = driver.execute_script("return document.body.scrollHeight")  
                if new_height == last_height:  
                    logger.info("We have no new data. Choice is set as scroll\n")
                    break  
                last_height = new_height  

        if view_type == "exception":
            domain = get_domain_from_url(url)
            driver.get(url)
            time.sleep(10)

            while True:
                self.page_consider = self.get_article_data_from_one_page(driver, db, url, view_type, parse_type, days_behind)
                if self.page_consider == 0:
                    logger.info(f"We can't find any new article in this exception case. Stop searching and try to get more artilces.\n")
                    break
                if get_more_articles(driver, domain) == 0:
                    self.page_consider = 0
                else:
                    logger.info(f"More articles are found in this exception case!!!\n")
                 
        driver.quit()
    
    def main(self):
        inputs = [ 
            {"url": "https://x.com/av24org", "view_type": "scroll", "parse_type": "//*[@data-testid='tweet']"},  
            {"url": "https://x.com/newstart_2024", "view_type": "scroll", "parse_type": "//*[@data-testid='tweet']"},  
            {"url": "https://x.com/school0fhealth", "view_type": "scroll", "parse_type": "//*[@data-testid='tweet']"},  
            {"url": "https://x.com/ifixhearts", "view_type": "scroll", "parse_type": "//*[@data-testid='tweet']"},  
            {"url": "https://x.com/plantparadise7", "view_type": "scroll", "parse_type": "//*[@data-testid='tweet']"},  
            {"url": "https://x.com/maryhollandnyc", "view_type": "scroll", "parse_type": "//*[@data-testid='tweet']"},  
            {"url": "https://x.com/standforhealth1", "view_type": "scroll", "parse_type": "//*[@data-testid='tweet']"},  
            {"url": "https://x.com/bryanardisx", "view_type": "scroll", "parse_type": "//*[@data-testid='tweet']"},  
        ]
        # Create a new file (or overwrite if it already exists)  
        with open("log.txt", "w") as file:  
            file.write("This is a log file.\n")  

        for input in inputs:
            try:
                db = self.db_general

                url = input["url"]
                view_type = input["view_type"]
                parse_type = input["parse_type"]

                article_domain = get_domain_from_url(url)
                if article_domain in self.view_exceptions:
                    view_type = "exception"
                    logger.info("We found exception cases!!!")
                
                logger.info(article_domain)
                logger.info(f"\033[1;36m We are handling Completely different new url. Current url: {url}\033[0m")  
                
                driver = self.setup_driver(url)
                try:
                    if input["article_type"] == "video":
                        logger.info("DB is set as Video.")
                        db = self.db_video
                except:
                    logger.info("No Video DB is set.")
                
                if article_domain == "x.com" or "twitter.com":
                    logger.info("DB is set as X.")
                    db = self.db_x
                    x_sign_in(driver)
                    driver.save_screenshot("screenshot/X-Sign-in.png")
                else:
                    logger.info("No X DB is set.")
                
                self.consider_exit = 0
                whole_article_data = self.get_whole_article_data(driver, db, url, view_type, parse_type, days_behind=7)

                with open(f"output/{article_domain}.json", 'w', encoding='utf-8') as f:
                    json.dump(whole_article_data, f, ensure_ascii=False, indent=4)
            except Exception as e:
                logger.error(f"An error occurred: {e} in url: {url}")
                with open("log1.txt", "a") as file:
                    file.write(f"Error: {e} in url: {url}\n")
                
if __name__ == "__main__":
    general_scrapper = Generalscrapper()
    general_scrapper.main()