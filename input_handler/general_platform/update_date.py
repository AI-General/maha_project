# import firebase related libraries
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
from datetime import datetime  
from twitter import is_twitter_url
# import environment libraries
from dotenv import load_dotenv  # Import the dotenv support  
load_dotenv()

from db import initialize_firestore
db = initialize_firestore("Firebase_Credentials_General_Platform", app_name="General_Platform")

# Today's date  
today_date = datetime.now().strftime("%Y-%m-%d")  # Format today's date as YYYY-MM-DD               
                        
# Function to process all documents in a collection  
def process_collection(collection_name):  
    print(f"Processing collection: {collection_name}")  
    
    # Retrieve all documents in the collection  
    docs = db.collection(collection_name).stream()  

    for doc in docs:  
        doc_data = doc.to_dict()  # Convert document to dict  
        # Check if the `article_age` field is empty  
        if doc_data.get('article_age') == "":  # Field doesn't exist, is empty, or null  
            # Create new value for the field  
            new_value = f"*** {today_date}"  

            # Update the document  
            db.collection(collection_name).document(doc.id).update({  
                'article_age': new_value  
            })  

            print(f"Updated document '{doc.id}' in collection '{collection_name}' with article_age='{new_value}'")  

# List all collections in the database  
collections = db.collections()  

# Process each collection  
for collection in collections:  
    process_collection(collection.id)  

print("Update process completed!")  