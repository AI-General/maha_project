import requests  

short_url = "https://t.co/21eE0oDiLn"  
response = requests.head(short_url, allow_redirects=True)  
direct_url = response.url  
print(direct_url)