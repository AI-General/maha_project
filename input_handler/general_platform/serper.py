# serper.py
# import default libraries
import http.client
import json
import sys
import os

# import environment libraries
from dotenv import load_dotenv
load_dotenv()

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

# import function from other filie
from parse_utils import parse_post_date

conn = http.client.HTTPSConnection("scrape.serper.dev")
headers = {
  'X-API-KEY': os.getenv("SERPER_API_KEY"),
  'Content-Type': 'application/json'
}

def get_date_from_serper(article_dict):  
    for key, value in article_dict["metadata"].items():  
        if "time" in key.lower():  # Case-insensitive check for "time" in the key  
            try:  
                date_str = parse_post_date(value)  
                return date_str
            except Exception as e:  
                logger.info(f"Error parsing the time value for key '{key}': {e}")  
                return "" 
    return ""

def get_article_info_from_serper(url):
  payload = json.dumps({
    "url": f"{url}"
  })
  conn.request("POST", "/", payload, headers)
  res = conn.getresponse()
  data = res.read()
  logger.info("Serper API Key: " + os.getenv("SERPER_API_KEY"))
  article_dict = {}
  try:  
      article_dict = json.loads(data.decode("utf-8"))  # Decode response to string and then parse JSON 
  except Exception as e:  
    logger.error(f"Error decoding the response: {e}")
    with open("log.txt", "a") as file:
      file.write(f"Error: {e})\n")
    return "", ""
  
  text = ""  
  date = ""
  try:
    text = article_dict["text"]
  except Exception as e:
    logger.error(f"Error getting the text: {e}")

  try:
    date = get_date_from_serper(article_dict)
  except Exception as e:
    logger.info(f"Error getting the date: {e}")

  return text, date