import os
import sys
from loguru import logger
from dotenv import load_dotenv  # Import the dotenv support  

import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore

load_dotenv()

def initialize_firestore(firebase_project_id, app_name=None):  
    GOOGLE_APPLICATION_CREDENTIALS = os.getenv(f"{firebase_project_id}")
    cred = credentials.Certificate(GOOGLE_APPLICATION_CREDENTIALS)
    app = firebase_admin.initialize_app(cred, name=app_name)  # Pass a unique app_name  
    return firestore.client(app)  

logger.configure(handlers=[{  
    "sink": sys.stdout,  
    "format": "<yellow>{time:YYYY-MM-DD HH:mm:ss}</yellow> | "  
            "<level>{level}</level> | "  
            "<cyan>{module}</cyan>:<cyan>{function}</cyan> | "  
            "<yellow>{message}</yellow>",  
    "colorize": True   
}])  

def get_single_article(db,article_domain, article_title):
    article = db.collection(f"{article_domain}").document(article_title).get()
    if not article.exists:
        return None
    return article.to_dict()

def check_if_exists(db, article_domain, article):
    """Check if the article already exists in the database."""
    if get_single_article(db,article_domain, article["article_title"]) is not None:
        print(f"""Article "{article["article_title"]}" already exists\n""")
        return True
    return False

def force_insert_article(db, article_domain, article):
    db.collection(f"{article_domain}").document(article["article_title"]).set(article)

def insert_article(db, article_domain, article):
    """Insert the article into the database."""
    try:
        # article_parsed = articles_model.Case.model_validate(article)
        if check_if_exists(db, article_domain, article):
            return
        force_insert_article(db, article_domain, article)
        print(f"Succeeded to insert article {article['article_title']}")
        key_to_exclude = "text"  

        # Create a new dictionary excluding the specified key  
        article_without_text = {key: value for key, value in article.items() if key != key_to_exclude}  

        # Print the new dictionary 
        print(f"{article_without_text}\n")
    except Exception as e:
        print(f"Failed to insert article {article['article_title']}: {e}")
