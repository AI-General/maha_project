import re
import base64
from urllib.parse import urlparse, urlunparse, parse_qs, urlencode

def get_domain_from_url(
    url: str,
) -> str:
    domain = urlparse(url).netloc
    if "www." in domain:
        domain = domain.replace("www.", "")

    return domain

def decode_url(url):
    # Parse the URL
    parsed_url = urlparse(url)
    file_extensions_to_strip_query = [".mp3", ".wav", ".mp4", ".avi"]

    # Special processing for specific file extensions with query parameters (Azure SAS Tokens)
    if any(parsed_url.path.endswith(ext) for ext in file_extensions_to_strip_query):
        # Parse query parameters
        query_params = parse_qs(parsed_url.query)

        # Reconstruct the full URL without the query parameters
        new_url_components = parsed_url._replace(query="")
        new_url = urlunparse(new_url_components)
        return new_url

    # Preserve the existing logic for other cases

    # Parse the query parameters
    query_params = parse_qs(parsed_url.query)

    # Decode the referrer if it exists
    if "referrer" in query_params:
        encoded_referrer = query_params["referrer"][0]
        decoded_referrer_bytes = base64.urlsafe_b64decode(encoded_referrer + "==")
        decoded_referrer = decoded_referrer_bytes.decode("utf-8")
        query_params["referrer"] = [decoded_referrer]

    # Reconstruct the query string
    encoded_query = urlencode(query_params, doseq=True)

    # Reconstruct the full URL
    new_url_components = parsed_url._replace(query=encoded_query)
    new_url = urlunparse(new_url_components)

    return new_url

def parse_youtube_url(url: str) -> str:  
    youtube_domains = [  
        "youtube.com",  
        "m.youtube.com",  
        "youtu.be",  
    ]  
    
    # Check if the URL is from a recognized YouTube domain.  
    domain = urlparse(url).netloc  
    if domain not in youtube_domains and not domain.endswith(".youtube.com"):  
        raise ValueError("The URL does not belong to a recognized YouTube domain.")  

    if "youtu.be" in url:  
        # Assuming URL is of the form https://youtu.be/VIDEO_ID  
        path_segments = urlparse(url).path.split('/')  
        if len(path_segments) > 1:  
            # The YouTube video ID should be directly after the slash  
            video_id = path_segments[1]  
        else:  
            raise ValueError("Invalid YouTube 'youtu.be' URL format.")  
    else:  
        # Assuming URL is of the form https://www.youtube.com/watch?v=VIDEO_ID or similar  
        query_string = urlparse(url).query  
        video_id = parse_qs(query_string).get("v")  
        # If the video_id is a list, convert it to a string  
        if isinstance(video_id, list):  
            video_id = video_id[0]  
        elif video_id is None:  
            raise ValueError("Video ID not found in the URL.")  
    
    # Validate the extracted video ID  
    if not re.match(r'^[0-9A-Za-z_-]{11}$', video_id):  
        raise ValueError("Invalid YouTube video ID.")  
    
    return video_id  
