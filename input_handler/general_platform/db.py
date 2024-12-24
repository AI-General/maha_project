# db.py
# import default libraries
import os
import sys

# import firebase related libraries
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore

# import environment libraries
from dotenv import load_dotenv  # Import the dotenv support  
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

def initialize_firestore(firebase_project_id, app_name=None):  
    GOOGLE_APPLICATION_CREDENTIALS = os.getenv(f"{firebase_project_id}")
    cred = credentials.Certificate(GOOGLE_APPLICATION_CREDENTIALS)
    app = firebase_admin.initialize_app(cred, name=app_name)
    return firestore.client(app)  

def get_single_article(db, article_domain, article_title):
    article = db.collection(f"{article_domain}").document(article_title).get()
    if not article.exists:
        return None
    return article.to_dict()

def check_if_exists(db, article_domain, article_title):
    if get_single_article(db,article_domain, article_title) is not None:
        logger.info(f"""Article "{article_title}" already exists\n""")
        return True
    return False

def force_insert_article(db, article_domain, article):
    db.collection(f"{article_domain}").document(article["article_title"]).set(article)

def insert_article(db, article_domain, article):
    try:
        if check_if_exists(db, article_domain, article["article_title"]):
            return
        force_insert_article(db, article_domain, article)
        logger.info(f"Succeeded to insert article {article['article_title']}")

        # Print the article without the 'text' key for debugging
        article_without_text = {key: value for key, value in article.items() if key != "text"}  
        print(f"{article_without_text}\n")
    except Exception as e:
        logger.info(f"Failed to insert article {article['article_title']}: {e}")