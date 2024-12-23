import os  
import json
import sys
import requests  
from dotenv import load_dotenv

load_dotenv()

from urllib.parse import urlparse
from loguru import logger
from datetime import datetime, timedelta  
from dateutil.relativedelta import relativedelta  
import openai  

openai.api_key = os.getenv("OPENAI_API_KEY")  

logger.configure(handlers=[{  
    "sink": sys.stdout,  
    "format": "<yellow>{time:YYYY-MM-DD HH:mm:ss}</yellow> | "  
              "<level>{level}</level> | "  
              "<cyan>{module}</cyan>:<cyan>{function}</cyan> | "  
              "<yellow>{message}</yellow>",  
    "colorize": True   
}])  

def get_domain_from_url(url) -> str:
    domain = urlparse(url).netloc
    if "www." in domain:
        domain = domain.replace("www.", "")

    return domain

def convert_twitter_media_url(url):  
    base_url = url.split('?')[0]  
    if not base_url.endswith(".jpg"):  
        base_url += ".jpg"  
    
    return base_url

def check_url_status(url):  
    try:  
        response = requests.get(url, timeout=5)  # Timeout set to 5 seconds  
        if response.status_code == 200:  
            return 1  
        else:  
            return 0
    except requests.exceptions.RequestException as e:  
        return 0

def clean_article_url(article_url, article_image_url, url_domain):
    logger.info("Before cleaning article_url: " + article_url)
    logger.info("Before cleaning article_image_url: " + article_image_url)
    if not article_url.startswith("www") and not article_url.startswith("http") and not article_url.startswith("//www"):
        if not article_url.startswith("https"):
            if article_url.startswith(url_domain):
                article_url = "https://" + article_url
            
            if not article_url.startswith("/"):
                article_url = "https://" + url_domain + "/" + article_url
            else:
                article_url = "https://" + url_domain + article_url
    
    if not article_image_url.startswith("www") and not article_image_url.startswith("http") and not article_image_url.startswith("//www"):
        if not article_image_url.startswith("https"):
            if article_image_url.startswith(url_domain):
                article_image_url = "https://" + article_image_url

            if not article_image_url.startswith("/"):
                article_image_url = "https://" + url_domain + "/" + article_image_url
            else:
                article_image_url = "https://" + url_domain + article_image_url[1:]
    

    if article_image_url.startswith("https://pbs.twimg.com/media/"):
        logger.info("Changing Twitter urls to jpg format")
        if not article_image_url.endswith(".jpg"):
            article_image_url = convert_twitter_media_url(article_image_url)

    image_extensions = (  
        "jpg", "jpeg", "png", "gif", "bmp", "tiff", "tif", "svg", "webp", "ico",  
        "jfif", "pjpeg", "pjp", "avif", "heif", "heic", "raw", "cr2", "nef", "orf",  
        "sr2", "arw", "dng", "rw2", "pef", "raf", "3fr", "eip", "mrw", "nrw",  
        "x3f", "webp2"  
    )  

    if not article_image_url.lower().endswith(image_extensions):  
        # logger.info(f"article_image_url - {article_data['article_image_url']}")
        article_image_url = ""

    #  The order should be from bigger to smaller.
    replace_list = ["www.example.com", "yourwebsite.com", "examplewebsite.com", "example.com","website.com", "platform.com"]
    for item in replace_list:
        if item in article_url:
            article_url = article_url.replace(item, url_domain)
        if item in article_image_url:
            article_image_url = article_image_url.replace(item, url_domain)

    logger.info(f"article_url: {article_url}")
    logger.info(f"article_image_url: {article_image_url}")
    logger.info(f"url_domain: {url_domain}")
    return article_url, article_image_url

def parse_html(post_html):
    openai.api_key = os.getenv('OPENAI_API_KEY')  

    with open("prompt/parse_html.txt", "r") as file:  
        parse_html_prompt = file.read()

    with open("log.txt", "a") as f:
        f.write("\n************************************str(post_html)\n************************************\n")

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
        # Parse the "yyyy-mm-dd" date into a datetime object  
        article_date_obj = datetime.strptime(article_date, "%Y-%m-%d")  
        
        # Get today's date  
        today = datetime.today()  
        
        # Calculate the difference in days  
        days_behind = (today - article_date_obj).days  
        
        return days_behind  
    except ValueError as e:  
        return 999999    # If no matching article, append the new one  

def is_cloudflare_protected(url):  
    try:  
        # Send a GET request to the URL  
        response = requests.get(url, timeout=10)  
        
        # Check HTTP response headers for Cloudflare identification  
        if 'Server' in response.headers and 'cloudflare' in response.headers['Server'].lower():  
            return True  
        
        if 'CF-RAY' in response.headers:  
            return True  # Cloudflare adds a CF-RAY header to all responses.  

        # Check if body contains Cloudflare challenge page content  
        if "Redirecting..." in response.text and "/cdn-cgi/" in response.text:  
            return True  
        
        # If none of the above conditions are met, it's likely not Cloudflare-protected  
        return False  
    except requests.exceptions.RequestException as e:  
        print(f"Failed to connect to {url}: {e}")  
        return False  
