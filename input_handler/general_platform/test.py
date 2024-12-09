import time  
import sys
import json  
import re

from dotenv import load_dotenv
load_dotenv()

from selenium import webdriver  
from selenium.webdriver.chrome.service import Service  
from selenium.webdriver.common.by import By  
from selenium.webdriver.support.ui import WebDriverWait  
from selenium.webdriver.support import expected_conditions as EC  
from webdriver_manager.chrome import ChromeDriverManager  

from db import insert_article, check_if_exists
from serper import get_article_info_from_serper
from parse_utils import (  
    clean_article_url,  
    get_domain_from_url,
    parse_html,  
    parse_post_date,  
    calculate_days_behind,  
)
from exception_case import get_more_articles

file = open("program_log.log", "w")  
from loguru import logger
logger.configure(handlers=[{  
    "sink": sys.stdout,  
    "format": "<yellow>{time:YYYY-MM-DD HH:mm:ss}</yellow> | "  
            "<level>{level}</level> | "  
            "<cyan>{module}</cyan>:<cyan>{function}</cyan> | "  
            "<yellow>{message}</yellow>",  
    "colorize": True   
},
{  
    "sink": file,  
    "format": "<yellow>{time:YYYY-MM-DD HH:mm:ss}</yellow> | "  
            "<level>{level}</level> | "  
            "<cyan>{module}</cyan>:<cyan>{function}</cyan> | "  
            "<yellow>{message}</yellow>",  
    "colorize": True   
}])  

class Generalscrapper():
    def setup_driver(self):
        chrome_options = webdriver.ChromeOptions()  
        chrome_options.add_argument('--headless')  # Run in headless mode (no browser window)  
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
        
        webdriver_service = Service(ChromeDriverManager().install())
        return webdriver.Chrome(service=webdriver_service, options = chrome_options)

    def get_one_article_data(self, element, article_domain):
        article_data = []
        upper_trying_count = 0
        while True:
            if upper_trying_count == 5:
                logger.info("Tried 5 times to upper level. But couldn't find actual article")
                break            
            try:            
                post_html = element.get_attribute("outerHTML")  
            except Exception as e:
                post_html = ""            
            article_data = parse_html(post_html)
            if article_data["article_url"] and article_data["article_title"]:
                # Clean title of article
                sanitized_title = re.sub(r'[/*~[\]<>]', '', article_data["article_title"])  
                sanitized_title = sanitized_title.strip() 
                article_data["article_title"] = sanitized_title

                # logger.info("Found actual article_information")
                article_data["article_url"], article_data["article_image_url"] = clean_article_url(article_data["article_url"], article_data["article_image_url"], article_domain)
                break
            else:
                article_data = []
                try: 
                    element = element.find_element(By.XPATH, './..') 
                except Exception as e:
                    logger.info(f"Couldn't find any parent element: {e}")
                    break
                with open("log.txt", "a") as f:
                    f.write(f"\nDidn't found, dive deep one level more- {upper_trying_count}\n")
                upper_trying_count += 1
                continue
        
        return article_data

    def get_article_data_from_one_page(self, driver, url, view_type, parse_type, days_behind): 
        logger.info(f"\033[31m We are handling new url in same domain. Current url: {url}\033[0m")
        self.page_consider = 0
        self.exception_list = ["scroll", "exception"]
        if view_type not in self.exception_list:
            driver.get(url)  
        article_domain = get_domain_from_url(url)

        logger.info(f"Current URL - {url}")
        logger.info(f"Our main domain is - {article_domain}")
        time.sleep(10)
        WebDriverWait(driver, 20).until(lambda d: d.execute_script("return document.readyState") == "complete")  

    # try:  
        elements = driver.find_elements(By.XPATH, parse_type)   
        
        # If elements are found, process them  
        if elements:  
            logger.info(f"len(elements): {len(elements)}")  

            # Iterate over all elements and process data extraction  
            for element in elements:                                  
                article_data = self.get_one_article_data(element, article_domain) 
                
                if article_data == []:
                    logger.info("Couldn't find actual article from the element")                    
                    continue

                if article_data["article_url"] and article_data["article_title"]:  
                    if check_if_exists(article_domain, article_data):
                        continue

                    temp_age = article_data["article_age"]
                    article_data["text"], article_data["article_age"] = get_article_info_from_serper(article_data["article_url"])

                    if article_data["article_age"] == "":
                        logger.info(f"Serper api failed. Using post date - {temp_age}")
                        article_data["article_age"] = parse_post_date(temp_age)
                        
                    if article_data["article_age"] != "":
                        if calculate_days_behind(article_data["article_age"]) > days_behind:
                            logger.info(f"Article is older than {days_behind} days. Skipping\n")
                            continue
                    
                    insert_article(article_domain, article_data)               
                    self.page_consider += 1
                
        # except Exception as e:  
        #     logger.error(f"Error processing {url}: {e}", exc_info=True)
             
        return self.page_consider

    def get_whole_article_data(self, driver, url, view_type, parse_type, days_behind):
        base_url = url
        page_num = 1
        if view_type == "page1":
            if get_domain_from_url(url) == "thelibertydaily.com":
                logger.info(f"We met a special case - {url}")
                page_num = 5
                url = f"{base_url}/page/{page_num}/"
        # try:
            while True:
                self.page_consider = self.get_article_data_from_one_page(driver, url, view_type, parse_type, days_behind)
                if self.page_consider == 0:
                    logger.info(f"We can't find any new article in page {page_num}. Stop searching and choice is set as page1\n")
                    break
                page_num += 1
                url = f"{base_url}/page/{page_num}/"
            # except Exception as e:
            #     logger.error(f"An error occurred in page type 1: {e}", exc_info=True)
            
        if view_type == "page2":
            # try:
            while True:
                self.page_consider = self.get_article_data_from_one_page(driver, url, view_type, parse_type, days_behind)
                if self.page_consider == 0:
                    logger.info(f"We can't find any new article in page {page_num}. Stop searching and choice is set as page2\n")
                    break
                page_num += 1
                url = f"{base_url}?page={page_num}/"
            # except Exception as e:
            #     logger.error(f"An error occurred in page type 2: {e}", exc_info=True)
            
        if view_type == "scroll":
            # try:  
            last_height = driver.execute_script("return document.body.scrollHeight")  
            url = base_url
            driver.get(url)
            while True:    
                time.sleep(10)  # Adjust this value based on the site's load time  
                
                # Extract articles from the current page  
                self.page_consider = self.get_article_data_from_one_page(driver, url, view_type, parse_type, days_behind)  
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
            # except Exception as e:  
            #     logger.error(f"An error occurred: {e} while parsing in scroll mode.", exc_info=True)  

        if view_type == "exception":
            domain = get_domain_from_url(url)
            while True:
                self.page_consider = self.get_article_data_from_one_page(driver, url, view_type, parse_type, days_behind)
                if self.page_consider == 0:
                    logger.info(f"We can't find any new article in this exception case. Stop searching and try to get more artilces.\n")
                    break
                if get_more_articles(driver, domain) == 0:
                    self.page_consider = 0
                else:
                    logger.info(f"More articles are found in this exception case!!!\n")
                    parse_type = "//div[contains(@class, 'o-post-card') and contains(@class, 'o-post-card--inline')]"
                    elements = driver.find_elements(By.XPATH, parse_type)  
                    logger.info(f"Number of elements: {len(elements)}")
                    
            # except Exception as e:
            #     logger.error(f"An error occurred in page type 2: {e}", exc_info=True)
            
        driver.quit()
    

    def main(self):
        inputs = [{"url": "https://www.theamericanconservative.com/blogs/state_of_the_union/", "view_type": "button1", "parse_type": "//div[contains(@class, 'o-post-card') and contains(@class, 'o-post-card--inline')]"
        },]

        exceptions = ["theamericanconservative.com"]
        for input in inputs:
            url = input["url"]
            view_type = input["view_type"]
            parse_type = input["parse_type"]
            article_domain = get_domain_from_url(url)

            if article_domain in exceptions:
                view_type = "exception"
                logger.info("We found exception cases!!!")
            
            logger.info(f"\033[1;36m We are handling Completely different new url. Current url: {url}\033[0m")  
            driver = self.setup_driver()
            whole_article_data = self.get_whole_article_data(driver, url, view_type, parse_type, days_behind=10)

            with open(f"output/{article_domain}.json", 'w', encoding='utf-8') as f:
                json.dump(whole_article_data, f, ensure_ascii=False, indent=4)

if __name__ == "__main__":
    general_scrapper = Generalscrapper()
    general_scrapper.main()