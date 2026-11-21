import requests

def get_warrior_plus_products(api_key, account_id, limit=10):
    """Get products from Warrior Plus API."""
    try:
        url = "https://warriorplus.com/api/v2/marketplace/search"
       
        # Make sure the parameter names exactly match what the API expects
        params = {
            "api_key": api_key,
            "account_id": account_id,
            "limit": str(limit),  # Convert to string to be safe
            "sort_by": "conversion_rate"
        }
       
        print(f"Sending request with params: {params}")
       
        response = requests.get(url, params=params)
       
        # Print response for debugging
        print(f"Response status code: {response.status_code}")
        print(f"Response content: {response.text[:200]}...")  # Print first 200 chars
       
        response.raise_for_status()
        return response.json().get("products", [])
      
    except Exception as e:
        print(f"Error getting products: {str(e)}")
        return []

# Test the function
if __name__ == "__main__":
    API_KEY = "0102d96ea53b182e31ea534948eb89b"
    ACCOUNT_ID = "borggump"
  
    print("Attempting to fetch products from Warrior Plus...")
    products = get_warrior_plus_products(API_KEY, ACCOUNT_ID)
   
    if not products:
        print("No products found or API error occurred. Using mock data instead.")
        products = [
            {
                "id": "mock1",
                "name": "Ultimate Traffic Blueprint",
                "description": "Get unlimited traffic to your offers using this proven system.",
                "price": "$27.00"
            },
            {
                "id": "mock2",
                "name": "AI Content Creator Pro",
                "description": "Generate high-converting content in seconds with this AI tool.",
                "price": "$47.00"
            }
        ]
  
    print(f"Found {len(products)} products:")
    for product in products:
        print(f"- {product['name']}: {product['price']}")