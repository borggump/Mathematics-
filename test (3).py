import requests

def get_warrior_plus_products(api_key, account_id, limit=10):
    """Get products from Warrior Plus API."""
    try:
        url = "https://warriorplus.com/api/v2/marketplace/search"
        
        # Include parameters in the URL query
        params = {
            "account_id": account_id,
            "limit": str(limit),
            "sort_by": "conversion_rate"
        }
        
        # Add API key in headers instead
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        print(f"Sending request with headers: {headers}")
        print(f"And params: {params}")
        
        response = requests.get(url, headers=headers, params=params)
        
        print(f"Response status code: {response.status_code}")
        print(f"Response content: {response.text[:200]}...")
        
        response.raise_for_status()
        return response.json().get("products", [])
       
    except Exception as e:
        print(f"Error getting products: {str(e)}")
        return []