import http.client
import json
import sys
import os
from dotenv import load_dotenv
from datetime import datetime  
from parse_utils import parse_post_date
from loguru import logger

load_dotenv()

logger.configure(handlers=[{  
    "sink": sys.stdout,  
    "format": "<yellow>{time:YYYY-MM-DD HH:mm:ss}</yellow> | "  
            "<level>{level}</level> | "  
            "<cyan>{module}</cyan>:<cyan>{function}</cyan> | "  
            "<yellow>{message}</yellow>",  
    "colorize": True   
}])  

conn = http.client.HTTPSConnection("scrape.serper.dev")
headers = {
  'X-API-KEY': os.getenv("SERPER_API_KEY"),
  'Content-Type': 'application/json'
}

def get_date_from_serper(article_dict):  
    # Iterate through the dictionary to find the first "time" key  
    for key, value in article_dict["metadata"].items():  
        if "time" in key.lower():  # Case-insensitive check for "time" in the key  
            try:  
                # Attempt to parse using dateutil for flexibility  
                date_str = parse_post_date(value)  
                # Format it into "yyyy-mm-dd"  
                return date_str
            except Exception as e:  
                print(f"Error parsing the time value for key '{key}': {e}")  
                return "" 

    # If no key with "time" is found  
    return ""

def get_article_info_from_serper(url):
  payload = json.dumps({
    "url": f"{url}"
  })
  conn.request("POST", "/", payload, headers)
  res = conn.getresponse()
  data = res.read()
  logger.info("Serper API Key: " + os.getenv("SERPER_API_KEY"))

  # Decode the response and save it as a JSON file  
  try:  
      # Convert the response to a Python dictionary  
      article_dict = json.loads(data.decode("utf-8"))  # Decode response to string and then parse JSON  
      return article_dict["text"], get_date_from_serper(article_dict)
  except Exception as e:  
    print(f"Error decoding the response: {e}")
    return "", ""