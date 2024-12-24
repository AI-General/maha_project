# parse_utils.py
# import default libraries
import os  
import json
import sys
import requests  

# import openai related libraries 
import openai  
openai.api_key = os.getenv("OPENAI_API_KEY")  

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

# import date and url_parse libraries
from urllib.parse import urlparse
from datetime import datetime, timedelta  
from dateutil.relativedelta import relativedelta 

# import environment libraries
from dotenv import load_dotenv
load_dotenv()

def get_domain_from_url(url) -> str:
    domain = urlparse(url).netloc
    if "www." in domain:
        domain = domain.replace("www.", "")
    return domain

# Function to convert not properly formatted Twitter media URL to JPEG
def convert_twitter_media_url(url):  
    base_url = url.split('?')[0]  
    if not base_url.endswith(".jpg"):  
        base_url += ".jpg"  
    return base_url

def clean_article_url(article_url, article_image_url, url_domain):
    logger.info("Before cleaning article_url: " + article_url)
    logger.info("Before cleaning article_image_url: " + article_image_url)
    # print as while for debugging
    logger.info("\033[97m*********************************************************\033[0m")    
    
    # If article_url doesn't start with "www" or "http" or "//www"
    if not article_url.startswith("www") and not article_url.startswith("http") and not article_url.startswith("//www"):
        # Handles if article_url doesn't start with "https" but starts with url_domain
        if not article_url.startswith("https"):
            if article_url.startswith(url_domain):
                article_url = "https://" + article_url            
        # Assume the article_url is a relative URL, so if article_url doesn't start with "/", add "https://" and url_domainto the url
        else:
            if not article_url.startswith("/"):
                article_url = "https://" + url_domain + "/" + article_url
            else:
                article_url = "https://" + url_domain + article_url
    
    # If article_image_url doesn't start with "www" or "http" or "//www"
    if not article_image_url.startswith("www") and not article_image_url.startswith("http") and not article_image_url.startswith("//www"):
        # Handles if article_image_url doesn't start with "https" but starts with url_domain
        if not article_image_url.startswith("https"):
            if article_image_url.startswith(url_domain):
                article_image_url = "https://" + article_image_url

        # Assume the article_image_url is a relative URL, so if article_image_url doesn't start with "/", add "https://" and url_domain to the url
        else:
            if not article_image_url.startswith("/"):
                article_image_url = "https://" + url_domain + "/" + article_image_url
            else:
                logger.info("We appended / to article_image_url")
                article_image_url = "https://" + url_domain + article_image_url[1:]

    # If article_image_url starts with "https://pbs.twimg.com/media/" convert not properly formatted Twitter media URL to JPEG
    if article_image_url.startswith("https://pbs.twimg.com/media/"):
        logger.info("Changing Twitter urls to jpg format")
        if not article_image_url.endswith(".jpg"):
            article_image_url = convert_twitter_media_url(article_image_url)

    # Check if article_image_url is an image
    image_extensions = (  
        "jpg", "jpeg", "png", "gif", "bmp", "tiff", "tif", "svg", "webp", "ico",  
        "jfif", "pjpeg", "pjp", "avif", "heif", "heic", "raw", "cr2", "nef", "orf",  
        "sr2", "arw", "dng", "rw2", "pef", "raf", "3fr", "eip", "mrw", "nrw",  
        "x3f", "webp2"  
    )  
    if not article_image_url.lower().endswith(image_extensions):  
        logger.info(f"Currently article_image_url is not an image - {article_image_url}. Set as empty")
        article_image_url = ""

    # Change all instances of "www.example.com", "yourwebsite.com", "examplewebsite.com", "example.com", "website.com", "platform.com" to url_domain
    replace_list = ["www.example.com", "yourwebsite.com", "examplewebsite.com", "example.com","website.com", "platform.com"]
    for item in replace_list:
        if item in article_url:
            article_url = article_url.replace(item, url_domain)
        if item in article_image_url:
            article_image_url = article_image_url.replace(item, url_domain)

    logger.info(f"After cleaning article_url: {article_url}")
    logger.info(f"After cleaning article_image_url: {article_image_url}")
    logger.info(f"url_domain: {url_domain}")
    # print as while for debugging
    logger.info("\033[97m*********************************************************\033[0m")  
    return article_url, article_image_url

def parse_html(post_html):
    openai.api_key = os.getenv('OPENAI_API_KEY')  
    with open("prompt/parse_html.txt", "r") as file:  
        parse_html_prompt = file.read()

    response = openai.ChatCompletion.create(  
        model="gpt-4o-mini",   
        messages=[  
            {  
                "role": "system",  
                "content": f"{parse_html_prompt}"  # Pass the HTML parsing instructions to the system  
            },  
            {  
                "role": "user",  
                "content": f"target_html_contents - \n\n{str(post_html)}"  # Pass the HTML content for parsing  
            }  
        ],  
        response_format={  
            "type": "json_schema",  
            "json_schema": {  
                "name": "json_schema", 
                "schema": {  
                    "type": "object", 
                    "properties": {  
                        "article_title": {  
                            "type": "string",  
                            "description": "The title of the article"  
                        },  
                        "article_url": {  
                            "type": "string",  
                            "description": "The URL of the article"  
                        },  
                        "article_image_url": {  
                            "type": "string",  
                            "description": "The image URL for the article"  
                        },  
                        "short_article_description": {  
                            "type": "string",  
                            "description": "A short description of the article"  
                        },  
                        "article_age": {  
                            "type": "string",  
                            "description": "The age of the article (e.g., how many days ago it was published)"  
                        }  
                    },  
                    "required": [  # Specify which properties are mandatory  
                        "article_title",  
                        "article_url",  
                        "article_image_url",  
                        "short_article_description",  
                        "article_age"  
                    ]  
                }  
            }  
        }  
    )
    article_data = json.loads(response.choices[0].message.content)   
    return article_data

def parse_twitter_html(post_html):
    openai.api_key = os.getenv('OPENAI_API_KEY')  
    with open("prompt/parse_twitter_html.txt", "r") as file:  
        parse_html_prompt = file.read()

    response = openai.ChatCompletion.create(  
        model="gpt-4o-mini",   
        messages=[  
            {  
                "role": "system",  
                "content": f"{parse_html_prompt}"  # Pass the HTML parsing instructions to the system  
            },  
            {  
                "role": "user",  
                "content": f"target_html_contents - \n\n{str(post_html)}"  # Pass the HTML content for parsing  
            }  
        ],  
        response_format={  
            "type": "json_schema",  
            "json_schema": {  
                "name": "json_schema", 
                "schema": {  
                    "type": "object", 
                    "properties": {  
                        "article_title": {  
                            "type": "string",  
                            "description": "The title of the article"  
                        },  
                        "article_url": {  
                            "type": "string",  
                            "description": "The URL of the article"  
                        },  
                        "article_image_url": {  
                            "type": "string",  
                            "description": "The image URL for the tweet"  
                        },  
                        "short_article_description": {  
                            "type": "string",  
                            "description": "A short description of the tweet"  
                        },  
                        "article_age": {  
                            "type": "string",  
                            "description": "The age of the article (e.g., how many days ago it was published)"  
                        }  
                    },  
                    "required": [  # Specify which properties are mandatory  
                        "article_title",  
                        "article_url",  
                        "article_image_url",  
                        "article_description",  
                        "article_age"  
                    ]  
                }  
            }  
        }  
    )
    tweet_data = json.loads(response.choices[0].message.content)        
    return tweet_data

def parse_post_date(date_string):
    openai.api_key = os.getenv("OPENAI_API_KEY")  
    with open("prompt/parse_date.txt", "r") as file:  
        parse_date_prompt = file.read()

    with open("prompt/parse_old.txt", "r") as file:  
        parse_old_prompt = file.read()

    response = openai.ChatCompletion.create(  
        model="gpt-4o-2024-11-20",  
        messages=[  
            {  
                "role": "system",  
                "content": f"""{parse_date_prompt}"""  
            },  
            {  
                "role": "user",  
                "content": f"target_date_string:\n\n{str(date_string)}"  
            }  
        ]  
    )  

    response_string = response['choices'][0]['message']['content'].strip() 
    if response_string != '""':
        # logger.info("We should check how old the article is.")
        return response_string
    
    response = openai.ChatCompletion.create(  
        model="gpt-4o-2024-11-20",  
        messages=[  
            {  
                "role": "system",  
                "content": f"""{parse_old_prompt}"""  
            },  
            {  
                "role": "user",  
                "content": f"target_date_string: \n\n{str(date_string)}"  
            }
        ],
        response_format={  
            "type": "json_schema",  
            "json_schema": {  
                "name": "json_schema",  
                "schema": {  
                    "type": "object",  
                    "properties": {  
                        "year": {  
                            "type": "integer"  
                        },  
                        "month": {  
                            "type": "integer"  
                        },  
                        "day": {  
                            "type": "integer"  
                        },  
                        "hour": {  
                            "type": "integer"  
                        }
                    },  
                    "required": [  
                        "year",  
                        "month",  
                        "day",  
                        "hour",  
                        ]  
                }  
            }  
        }    
    )

    age_dict = json.loads(response.choices[0].message.content)
    none_flag = 0
    for key, value in age_dict.items():
        if value is not None:
            none_flag += 1
            break
    if none_flag == 0:
        return ""
    
    if age_dict:
        year = age_dict.get("year", 0) or 0  
        month = age_dict.get("month", 0) or 0  
        day = age_dict.get("day", 0) or 0  
        hour = age_dict.get("hour", 0) or 0  

        # Calculate the older date  
        current_date = datetime.now()  
        older_date = current_date - relativedelta(years=year, months=month)  
        older_date -= timedelta(days=day, hours=hour)  
        return older_date.strftime("%Y-%m-%d")  
    
    return ""

def calculate_days_behind(article_date):  
    try:  
        article_date_obj = datetime.strptime(article_date, "%Y-%m-%d")  
        today = datetime.today()  
        days_behind = (today - article_date_obj).days  
        
        return days_behind  
    except ValueError as e:  
        return 999999    # If no matching article, append the new one  

def is_cloudflare_protected(url):  
    try:  
        response = requests.get(url, timeout=10)  
        if 'Server' in response.headers and 'cloudflare' in response.headers['Server'].lower():  
            return True  
        
        if 'CF-RAY' in response.headers:  
            return True  # Cloudflare adds a CF-RAY header to all responses.  
        
        if "Redirecting..." in response.text and "/cdn-cgi/" in response.text:  
            return True  
        return False  
    except requests.exceptions.RequestException as e:  
        print(f"Failed to connect to {url}: {e}")  
        return False  