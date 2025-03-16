import requests
from bs4 import BeautifulSoup
import json
import os
import time
import random

from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_SERVICE_ROLE_API_KEY") # this key to bypass rls as i have it enabled
supabase: Client = create_client(url, key)

graphql_query = """
query NonCachedPage(
  $stagingHost: String, 
  $previewOptions: JSON, 
  $moduleParams: JSON, 
  $url: JSON
) {
  Page: NonCachedPage(
    stagingHost: $stagingHost, 
    previewOptions: $previewOptions, 
    moduleParams: $moduleParams, 
    url: $url
  ) {
    content
  }
}
"""

user_agents = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1",
    "PostmanClient/11.36.1 (AppId=14b197a5-79b1-46b6-b437-be2587eeca07"
]
 
def read_or_webscrape_urls(filename):
  ulta_product_urls = []
  
  if os.path.exists(filename):
    print("product_urls.txt exists, reading file")
    with open(filename, 'r') as file:
            ulta_product_urls = file.read().splitlines()
  else:
    ulta_product_urls = list(parse_ulta_sitemaps())  # Convert generator to list if needed
    with open(filename, "w") as file:
        for url in parse_ulta_sitemaps():  # Directly iterate over generator
            file.write(url + "\n")  # Write each URL on a new line
  
  return ulta_product_urls

def parse_ulta_sitemaps():
    session = requests.Session()  # Persistent session for efficiency
    ulta_sitemap = 'https://www.ulta.com/sitemap/p.xml'

    response = session.get(ulta_sitemap)
    soup = BeautifulSoup(response.text, 'xml')  # Faster XML parsing

    sitemap_urls = [loc.text for loc in soup.find_all('loc')]

    product_urls = set()  # Use a set to prevent duplicates

    for sitemap_url in sitemap_urls:
        response = session.get(sitemap_url)
        soup = BeautifulSoup(response.text, 'xml')

        for loc in soup.find_all('loc'):
            if 'image' not in loc.parent.name:  # Exclude image URLs
                url = loc.text.strip()
                if url not in product_urls:  # Check for duplicates
                    product_urls.add(url)
                    yield url  # Yield for memory efficiency

def query_ulta_graphql(product_url): #returns json
  session = requests.Session()
  retries = 3
  endpoint = "https://www.ulta.com/dxl/graphql?ultasite=en-us"
  # Headers to mimic Postman
  headers = {
    "Content-Type": "application/json; charset=utf-8",
    "User-Agent": random.choice(user_agents),
    "Accept": "*/*",
  }
  # Define variables (same as in Postman bc with out it i was unable to make the request)
  variables = {
      "moduleParams": {
          "gti": "f406ed7a-61c9-4cdb-bda9-1a5497e1acd5",
          "loginStatus": "anonymous"
      },
      "url": {"path": product_url}
  }
  for attempt in range(retries):
      response = session.post(endpoint, json={"query": graphql_query, "variables": variables}, headers=headers,timeout=30)
      
      if response.status_code == 200:
          print('200 OK')
          return response.json()
      
      elif response.status_code in [429, 403]:  # Rate limit or banned
          wait_time = (2 ** attempt) + random.uniform(0, 0.2)
          print(f"Rate limited. Retrying in {wait_time:.2f} seconds...")
          time.sleep(wait_time)
  print("Failed after retries. Skipping...")
  return

# def parse_responce(data,url): # returns dictionary
#   # Product = json.dumps(data)
#   Product= data
#   # ProductInformation = Product["data"]["Page"]["content"]["modules"][4]["modules"][1]
#   ProductPricing  = Product["data"]["Page"]["content"]["modules"][4]["modules"][3]

#   # ProductSummary = Product["data"]["Page"]["content"]["modules"][4]["modules"][4]
#   ProductDetail = Product["data"]["Page"]["content"]["modules"][4]["modules"][5]

#   ProductVariant = Product["data"]["Page"]["content"]["modules"][4]["modules"][6]
#   # ProductReviews = Product["data"]["Page"]["content"]["modules"][12]
  
#   payload = {
#         "url": url,
#         "name": ProductPricing["productName"],
#         "price": ProductPricing["dataCapture"]["dataLayer"]["Tealium"]["product_price"],
#         "size": ProductVariant["dimensionsValue"],
#         "variant": ProductPricing["variantLabel"],
#         "description": ProductDetail["description"],
#         "category": ProductPricing["productCategoryOne"],
#         "image_url": ProductPricing["image"]["imageUrl"],
#         "brand_name": ProductPricing["brandName"],
#         "scraped_from": 'ulta',
#         "usage": ProductDetail["usage"],
#         "ingredients": ProductDetail["ingredients"]
#     }

#   return payload

def parse_response(data, url):  # returns dictionary
    payload = {"url": url, "scraped_from": "ulta"}

    try:
        modules = data.get("data", {}).get("Page", {}).get("content", {}).get("modules", [])
        
        product_pricing = None
        product_detail = None
        product_variant = None

        if len(modules) > 4 and isinstance(modules[4].get("modules"), list):
            submodules = modules[4]["modules"]

            # Identify relevant modules dynamically
            for module in submodules:
                module_type = module.get("type", "")
                module_name = module.get("moduleName", "")

                if "ProductPricing" in module_type or "Pricing" in module_name:
                    product_pricing = module
                
                elif "ProductDetail" in module_type or "Detail" in module_name:
                    product_detail = module
                
                elif "ProductVariant" in module_type or "Variant" in module_name:
                    product_variant = module

        # Populate payload dynamically with safe access
        payload.update({
            "name": product_pricing.get("productName") if product_pricing else None,
            "price": (
                product_pricing.get("dataCapture", {})
                .get("dataLayer", {})
                .get("Tealium", {})
                .get("product_price")
                if product_pricing
                else None
            ),
            "size": product_variant.get("dimensionsValue") if product_variant else None,
            "variant": product_pricing.get("variantLabel") if product_pricing else None,
            "description": product_detail.get("description") if product_detail else None,
            "category": product_pricing.get("productCategoryOne") if product_pricing else None,
            "image_url": (
                product_pricing.get("image", {}).get("imageUrl")
                if product_pricing
                else None
            ),
            "brand_name": product_pricing.get("brandName") if product_pricing else None,
            "usage": product_detail.get("usage") if product_detail else None,
            "ingredients": product_detail.get("ingredients") if product_detail else None,
        })

        return payload

    except Exception as e:
        print(f"Error parsing response: {e}")
        return {"error": "Failed to parse response", "url": url}

  
def insert_if_not_exists(table_name, data_json, conflict_columns):
    try:
        # Check if the row already exists
        query = supabase.table(table_name).select("*").match({
            col: data_json[col] for col in conflict_columns
        }).execute()

        if query.data:  # If data is found, row already exists
            print("Row already exists. Skipping insert.")
        else:
            # Insert the new row
            result = supabase.table(table_name).insert(data_json).execute()

            if result and hasattr(result, "error") and result.error:
                raise result.error
            else:
                print("Row inserted successfully.")

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
  master_product_urls = 'product_urls.txt'
  ulta_product_urls = read_or_webscrape_urls(master_product_urls)
            
  print(f"Total unique product URLs: {len(ulta_product_urls)}")
   
  response = requests.get(ulta_product_urls[36], timeout=None)
  print(ulta_product_urls[36])
  soup = BeautifulSoup(response.text, 'html')  # Faster XML parsing
  with open('otherhtmltest.test', "w") as file: # Directly iterate over generator
        file.write(soup.text)
  print(soup.text)
# for product_url in ulta_product_urls:
#   data = query_ulta_graphql(product_url)
#   payload = parse_response(data,product_url)
#   insert_if_not_exists('product', payload, ["url"])
