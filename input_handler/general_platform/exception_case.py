# exception_case.py
# import default libraries 
import time  
import sys

# import selenium related libraries
from selenium import webdriver  
from selenium.webdriver.common.by import By  
from selenium.webdriver.common.action_chains import ActionChains  
from selenium.webdriver.support.ui import WebDriverWait  
from selenium.webdriver.support import expected_conditions as EC 

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

def get_more_articles(driver, domain):
    logger.info(f"Current domain is {domain}")
    if domain == "theamericanconservative.com":
        time.sleep(3)  
        try:  
            # Scrool Into View and waits for next action such as click
            wait = WebDriverWait(driver, 10)
            load_more_button = wait.until(EC.presence_of_element_located((By.CLASS_NAME, "js-archive-load-more-button")))  
            logger.info("Load more button found in the DOM!")  

            driver.execute_script("arguments[0].scrollIntoView(true);", load_more_button)  
            time.sleep(1)
  
            # Handle modal overlay (e.g., fc-dialog-scrollable-content)  
            try:  
                blocking_modal = driver.find_element(By.CLASS_NAME, "fc-dialog-scrollable-content")  
                driver.execute_script("arguments[0].style.display = 'none';", blocking_modal)  
                logger.info("Blocking modal hidden!")  
            except Exception as e:  
                logger.error(f"No blocking modal detected: {e}")  

            # Hide all iframes dynamically (if present)  
            iframes = driver.find_elements(By.TAG_NAME, "iframe")  
            for iframe in iframes:  
                try:  
                    iframe_id = iframe.get_attribute("id")  
                    logger.info(f"Hiding iframe with ID: {iframe_id}")  
                    driver.execute_script("arguments[0].style.display = 'none';", iframe)  
                except Exception as e:  
                    logger.error(f"Could not hide iframe: {e}")  

            # Check if the button is still blocked and force-click using JavaScript  
            try:  
                load_more_button.click()  
                logger.info("Button clicked successfully using Selenium!")  
            except Exception as e:  
                logger.error(f"Selenium click failed: {e}. Attempting JS-based click...")  
                driver.execute_script("arguments[0].click();", load_more_button)  # JS-based click fallback  
                
                logger.info("Button clicked successfully using JavaScript!")  

            time.sleep(10)  
        except Exception as e:  
            logger.error(f"An error occurred while loading more articles: {e}")  
            return 0
    elif domain == "nopharmfilm.com":
        time.sleep(3)
        try:  
            wait = WebDriverWait(driver, 10)  # Set a wait time of 10 seconds  
            load_more_button = wait.until(  
                EC.element_to_be_clickable((By.CLASS_NAME, "more-actions"))  
            )  
            load_more_button.click()  
            logger.info("Clicked 'Load more' button successfully.")           
        except Exception as e:  
            logger.error(f"An error occurred while loading more articles: {e}")  
            return 0
    elif domain == "podcasts.apple.com":
        # click see all button
        time.sleep(3)
        parent_element = driver.find_element(By.XPATH, "//div[@class='link-list svelte-12v9bo2']")  
        see_all_element = parent_element.find_element(By.XPATH, ".//a[@data-testid='click-action' and contains(text(), 'See All')]")  
        see_all_element.click()  
        logger.info("Clicked 'See All' button successfully.")