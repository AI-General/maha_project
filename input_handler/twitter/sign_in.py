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