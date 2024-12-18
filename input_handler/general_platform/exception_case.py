from selenium import webdriver  
from selenium.webdriver.common.by import By  
from selenium.webdriver.common.action_chains import ActionChains  
from selenium.webdriver.support.ui import WebDriverWait  
from selenium.webdriver.support import expected_conditions as EC  
import time  
import sys
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

# Initialize the WebDriver (Make sure to have the appropriate driver for your browser installed)  
driver = webdriver.Chrome()  # or webdriver.Firefox(), etc.  

def get_more_articles(driver, domain):
    logger.info(f"Current domain is {domain}")
    if domain == "theamericanconservative.com":
        time.sleep(3)  

        try:  
            # Step 1: Wait for the button to appear and become clickable  
            wait = WebDriverWait(driver, 10)  # Wait up to 10 seconds  
            load_more_button = wait.until(EC.presence_of_element_located((By.CLASS_NAME, "js-archive-load-more-button")))  
            print("Load more button found in the DOM!")  

            # Step 2: Scroll the button into view  
            driver.execute_script("arguments[0].scrollIntoView(true);", load_more_button)  
            time.sleep(1)  # Delay to ensure scrolling into view happens smoothly  

            # Step 3: Remove potential blocking elements (modal, overlays, iframes, etc.)  
            try:  
                # Handle modal overlay (e.g., fc-dialog-scrollable-content)  
                blocking_modal = driver.find_element(By.CLASS_NAME, "fc-dialog-scrollable-content")  
                driver.execute_script("arguments[0].style.display = 'none';", blocking_modal)  
                print("Blocking modal hidden!")  
            except Exception as e:  
                print(f"No blocking modal detected: {e}")  

            # Hide all iframes dynamically (if present)  
            iframes = driver.find_elements(By.TAG_NAME, "iframe")  
            for iframe in iframes:  
                try:  
                    iframe_id = iframe.get_attribute("id")  
                    print(f"Hiding iframe with ID: {iframe_id}")  
                    driver.execute_script("arguments[0].style.display = 'none';", iframe)  
                except Exception as e:  
                    print(f"Could not hide iframe: {e}")  

            # Check if the button is still blocked and force-click using JavaScript  
            try:  
                # Using normal Selenium click (preferred way)  
                load_more_button.click()  
                print("Button clicked successfully using Selenium!")  
            except Exception as e:  
                print(f"Selenium click failed: {e}. Attempting JS-based click...")  
                driver.execute_script("arguments[0].click();", load_more_button)  # JS-based click fallback  
                print("Button clicked successfully using JavaScript!")  

            # Optional: Allow some time for articles to load  
            time.sleep(10)  

        except Exception as e:  
            print(f"An error occurred while loading more articles: {e}")  
            return 0