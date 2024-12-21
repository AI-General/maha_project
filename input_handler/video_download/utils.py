import time
from urllib.parse import urlparse
from selenium.webdriver.support.ui import WebDriverWait  
from selenium.webdriver.support import expected_conditions as EC  
from selenium.webdriver.common.by import By

def get_domain_from_url(url) -> str:
    domain = urlparse(url).netloc
    if "www." in domain:
        domain = domain.replace("www.", "")

    return domain

def siginin(driver, url, domain):
    if domain == "podcasts.apple.com":
        try:  
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