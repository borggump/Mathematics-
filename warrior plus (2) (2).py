import requests

def get_warrior_plus_products(api_key, account_id, limit=10):
    """Get products from Warrior Plus API."""
    try:
        url = "https://warriorplus.com/api/v2/marketplace/search"
        params = {
            "0102d96ea53b182e31ea534948eb89b" : api_key,
            "borggump": account_id,
            "10": limit,
            "sort_by": "conversion_rate"
        }
       
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json().get("products", [])
       
    except Exception as e:
        print(f"Error getting products: {str(e)}")
        return []

# Test the function
if __name__ == "__main__":
    API_KEY = "0102d96ea53b182e31ea534948eb89b"
    ACCOUNT_ID = "borggump"
   
    # If no API key, use mock data
    if API_KEY == "0102d96ea53b182e31ea534948eb89b":
        print("Using mock data (no API key provided)")
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
    else:
        products = get_warrior_plus_products(API_KEY, ACCOUNT_ID)
   
    print(f"Found {len(products)} products:")
    for product in products:
        print(f"- {product['name']}: {product['price']}")
