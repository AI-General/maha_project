from selenium import webdriver  
from selenium.webdriver.common.by import By  
from selenium.webdriver.support.ui import WebDriverWait  
from selenium.webdriver.support import expected_conditions as EC  
from selenium.webdriver.chrome.service import Service  
from selenium.webdriver.common.keys import Keys  
import time  

# Step 1: Set up WebDriver (use ChromeDriver in this example)  
# Make sure to replace the path with the correct location of your `chromedriver`.  
chrome_option = webdriver.ChromeOptions()
chrome_option.add_argument('--headless')
driver = webdriver.Chrome(options=chrome_option)  


try:  
    # Step 2: Navigate to Twitter  
    driver.get("https://x.com/ResisttheMS")  

    # Optional: Maximize the window for better visibility  
    driver.maximize_window()  

    # Step 3: Login to Twitter (provide credentials if required)  
    # Note: Automating login is against Twitter's terms of service. If you're already logged in, skip this step.  
    time.sleep(5)  # Pause to wait if Twitter requires login (adjust timing as required)  

    # Step 4: Wait for tweets to load and find elements  
    ### Define the locator for tweets (using XPath for example)  
    tweet_xpath = "//*[@data-testid='tweet']"  

    ### Wait explicitly until at least one tweet is visible  
    WebDriverWait(driver, 10).until(  
        EC.presence_of_all_elements_located((By.XPATH, tweet_xpath))  
    )  

    # Find all tweet elements  
    tweets = driver.find_elements(By.XPATH, tweet_xpath)  
    print(f"Found {len(tweets)} tweets on the page.")  

    # Step 5: Extract text from tweets  
    for index, tweet in enumerate(tweets, start=1):  
        try:  
            # Get the visible text of the tweet  
            tweet_text = tweet.text  
            print(f"Tweet {index}: {tweet_text}")  
        except Exception as e:  
            print(f"Could not extract text from Tweet {index}: {e}")  

    # Step 6: Handle infinite scrolling (if required)  
    # Scroll down to load more tweets  
    SCROLL_PAUSE_TIME = 2  # Adjust pause time as needed  
    for _ in range(5):  # Scroll 5 times (adjust as needed)  
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")  
        time.sleep(SCROLL_PAUSE_TIME)  
        # Optional: Collect elements and process them here if needed  

except Exception as e:  
    print(f"An error occurred: {e}")  

finally:  
    # Step 7: Close the browser session  
    driver.quit()