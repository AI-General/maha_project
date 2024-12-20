import os
import re
import subprocess
import time
import requests
import yt_dlp
import base64

from typing import Callable, Dict, Optional, Tuple
from urllib.parse import urlparse, urlunparse, parse_qs, urlencode
from seleniumwire import webdriver  # Import from seleniumwire
from selenium.webdriver.common.action_chains import ActionChains  

from selenium.webdriver.common.by import By  
from selenium.webdriver.chrome.options import Options  
from selenium.webdriver.support.ui import WebDriverWait  
from selenium.webdriver.support import expected_conditions as EC  
from selenium.webdriver.chrome.service import Service  
from webdriver_manager.chrome import ChromeDriverManager 

from loguru import logger

def setup_driver():
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

def apple_siginin(driver, url):
    try:  
        driver.get(url)  # Replace with the actual URL  
        time.sleep(5)
            
        play_button = WebDriverWait(driver, 10).until(  
            EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Play')]"))  
        )  
        play_button.click()  
        print("Clicked the play button!")
        
        WebDriverWait(driver, 10).until(  
            EC.presence_of_element_located((By.CSS_SELECTOR, "dialog[data-testid='dialog'][open]"))  
        )  
        sign_in_button = WebDriverWait(driver, 10).until(  
            EC.element_to_be_clickable((By.CSS_SELECTOR, "button[data-testid='explicit-content-modal-action-button']"))  
        )  
        sign_in_button.click()  
        print("Clicked the 'Sign In' button!")
        time.sleep(10)

        iframe = WebDriverWait(driver, 10).until(  
            EC.presence_of_element_located((By.CSS_SELECTOR, "#ck-container iframe"))  
        )  
        driver.switch_to.frame(iframe)  
        print("Switched to the iframe!")    

        parent_container = WebDriverWait(driver, 10).until(  
            EC.presence_of_element_located((By.CSS_SELECTOR, "div[data-test='onboarding-commerce-form']"))  
        )  
        email_input = parent_container.find_element(By.ID, 'accountName')  
        email_input.click()  
        email_input.clear()  
        email_input.send_keys("nickfontana.tech@gmail.com")  
        print("Email input found and filled!")
        time.sleep(5)
            
        continue_button = WebDriverWait(driver, 10).until(  
            EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Continue')]"))  
        )  
        continue_button.click()
        print("Continue button found!")
        time.sleep(10)

        iframe = WebDriverWait(driver, 10).until(  
            EC.presence_of_element_located((By.CSS_SELECTOR, "iframe#aid-auth-widget-iFrame"))  
        )  
        driver.switch_to.frame(iframe)  
        print("Switched to second iframe!")
        
        password_input = WebDriverWait(driver, 10).until(  
            EC.presence_of_element_located((By.ID, 'password_text_field'))  
        )  
        password_input.click()  # Focus on the input field, may not be needed in some cases  
        password_input.clear()  # Clear any pre-existing text, if any  
        password_input.send_keys("P@ssw0rd123123")  # Input the password  
        time.sleep(5)
        
        sign_in_button = WebDriverWait(driver, 10).until(  
            EC.element_to_be_clickable((By.ID, 'sign-in'))  
        )  
        sign_in_button.click()  
        print("Clicked the 'Sign In' button!")  
        time.sleep(15)
        
        driver.get(url)
        resume_button = WebDriverWait(driver, 15).until(  
            EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Resume')]"))  
        )  
        resume_button.click()  
        print("Clicked the resume button!")
        time.sleep(15)
        
    except Exception as e:  
        print(f"An error occurred: {e}")  
        
def main():
    url = "https://podcasts.apple.com/us/podcast/268-dr-william-bays-historic-victory-over-ahpra-australian/id1687952188?i=1000680273675"
    driver = setup_driver()
    apple_siginin(driver, url)
    return

if __name__ == "__main__":
    main()