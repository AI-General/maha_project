# import firebase related libraries
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
from datetime import datetime  
from twitter import is_twitter_url, parse_tweet
# import environment libraries
from dotenv import load_dotenv  # Import the dotenv support  
load_dotenv()

from db import initialize_firestore
from parse_utils import clean_article_url, parse_post_date, get_domain_from_url 
db = initialize_firestore("Firebase_Credentials_X_Platform", app_name="X_Platform")

def process_collections():  
    # List all collections in the database  
    collections = db.collections()  

    for collection in collections:  
        print(f"Processing collection: {collection.id}")  
        # Fetch all documents in the collection  
        docs = collection.stream()  

        for doc in docs:  
            doc_data = doc.to_dict()  # Convert document to a dictionary  

            # Check if `article_url` contains a Twitter URL  
            article_url = doc_data.get('article_url')  
            if is_twitter_url(article_url):  
                # Check if `article_text` is empty  
                article_text = doc_data.get('text')  
                if article_text == "":  # Field is empty or null  
                    print(article_url)
                    age, text, image_url = parse_tweet(article_url)  
                    # Update Firestore document with the new data  
                    db.collection(collection.id).document(doc.id).update({  
                        "text": text
                    })  
                    print(f"Updated document '{doc.id}' in collection '{collection.id}':")  
                    print(f"article_text: {text}")
                    if doc_data.get('article_image_url') == "":
                        url_domain = get_domain_from_url(article_url)
                        article_url, image_url = clean_article_url(article_url, image_url, url_domain)
                        db.collection(collection.id).document(doc.id).update({  
                            "article_image_url": image_url
                        })  
                        print(f"article_image_url: {image_url}")
                    if doc_data.get('article_age') == "":
                        age = parse_post_date(age)
                        db.collection(collection.id).document(doc.id).update({  
                            "article_age": age
                        })  
                        print(f"article_age: {age}")
                    if not doc_data.get('article_age').startswith("2024-"): 
                        age = parse_post_date(age)
                        db.collection(collection.id).document(doc.id).update({  
                            "article_age": age
                        })  
                        print(f"Special article_age: {age}")

# Run the function  
process_collections()  

print("Processing completed!")