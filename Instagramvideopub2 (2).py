#!/usr/bin/env python3
"""
Warrior Plus to Instagram Automation (PyDroid3 version)
"""

import os
import time
import random
import json
import requests
from datetime import datetime, timedelta
import logging

# Set up logging to work on PyDroid3
# Use the current directory for logs instead of Termux path
script_dir = os.path.dirname(os.path.abspath(__file__))
log_file = os.path.join(script_dir, 'warrior_instagram_automation.log')

# Create logs directory if it doesn't exist
os.makedirs(os.path.dirname(log_file) if os.path.dirname(log_file) else '.', exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename=log_file
)
logger = logging.getLogger(__name__)

# Configuration
CONFIG = {
    "warrior_plus": {
        "api_key": "0102d96ea53b182e31ea534948eb89b",
        "account_id": "borggump",
        "focus_metrics": {
            "min_epc": 1.0,           # Minimum earnings per click
            "min_conversion": 5.0,    # Minimum conversion rate percentage
            "min_commission": 20.0,   # Minimum commission amount in dollars
            "preferred_categories": ["marketing", "software", "ecommerce"]
        }
    },
    "video_ai": {
        "provider": "synthesia",
        "api_key": "YOUR_VIDEO_AI_API_KEY",
    },
    "instagram": {
        "username": "YOUR_INSTAGRAM_USERNAME",
        "password": "YOUR_INSTAGRAM_PASSWORD",
    },
    "scheduling": {
        "min_hours_between_posts": 12,
        "max_hours_between_posts": 72,
        "posting_hours": range(8, 23),
        "days_of_week": [0, 1, 2, 3, 4, 5, 6],
    },
    "output_dir": os.path.join(script_dir, "warrior_videos")
}

# Ensure output directory exists
os.makedirs(CONFIG["output_dir"], exist_ok=True)


def notify_user(title, message):
    """Display notification to user in PyDroid3."""
    print(f"\n=== {title} ===")
    print(message)
    print("=" * (len(title) + 8))
    logger.info(f"Notification: {title} - {message}")


class WarriorPlusManager:
    """Handles interactions with Warrior Plus marketplace."""
    
    def __init__(self, config):
        self.api_key = config["warrior_plus"]["api_key"]
        self.account_id = config["warrior_plus"]["account_id"]
        self.focus_metrics = config["warrior_plus"]["focus_metrics"]
        self.base_url = "https://warriorplus.com/api/v2"
    
    def get_high_return_products(self, limit=10):
        """Fetch high-converting products with good ROI from Warrior Plus marketplace."""
        endpoint = f"{self.base_url}/marketplace/search"
        params = {
            "api_key": self.api_key,
            "account_id": self.account_id,
            "limit": limit,
            "sort_by": "conversion_rate",
            "min_epc": self.focus_metrics["min_epc"],
            "min_gravity": 10,
            "status": "active"
        }
        
        try:
            # For testing without API key, return mock data
            if self.api_key == "YOUR_WARRIOR_PLUS_API_KEY":
                logger.warning("Using mock data due to missing API key")
                return self.get_mock_products()
                
            response = requests.get(endpoint, params=params)
            response.raise_for_status()
            products = response.json().get("products", [])
            
            # Filter products by additional metrics
            high_return_products = []
            for product in products:
                # Calculate a "return potential score"
                conv_rate = float(product.get("conversion_rate", 0))
                epc = float(product.get("epc", 0))
                commission = float(product.get("commission_amount", 0))
                
                # Simple scoring algorithm
                return_score = (conv_rate * 0.4) + (epc * 0.4) + (commission * 0.2)
                
                product["return_score"] = return_score
                high_return_products.append(product)
            
            # Sort by custom return score
            sorted_products = sorted(high_return_products, key=lambda x: x["return_score"], reverse=True)
            
            logger.info(f"Found {len(sorted_products)} high-return products")
            return sorted_products
        except Exception as e:
            logger.error(f"Error fetching high-return products: {str(e)}")
            return self.get_mock_products()
    
    def get_mock_products(self):
        """Return mock product data for testing."""
        mock_products = [
            {
                "id": "mock1",
                "name": "Ultimate Traffic Blueprint",
                "description": "Get unlimited traffic to your offers using this proven system.",
                "price": "$27.00",
                "conversion_rate": 8.7,
                "epc": 2.4,
                "commission_amount": 22.50,
                "return_score": 3.2,
                "category": "marketing"
            },
            {
                "id": "mock2",
                "name": "AI Content Creator Pro",
                "description": "Generate high-converting content in seconds with this AI tool.",
                "price": "$47.00",
                "conversion_rate": 7.2,
                "epc": 3.1,
                "commission_amount": 35.00,
                "return_score": 4.1,
                "category": "software"
            },
            {
                "id": "mock3",
                "name": "Affiliate Commission Booster",
                "description": "Double your affiliate commissions with this simple strategy.",
                "price": "$37.00",
                "conversion_rate": 9.3,
                "epc": 2.8,
                "commission_amount": 25.00,
                "return_score": 3.8,
                "category": "marketing"
            }
        ]
        return mock_products
            
    def get_product_details(self, product_id):
        """Get detailed information about a specific product."""
        if product_id.startswith("mock"):
            # Return the mock product that matches the ID
            mock_products = self.get_mock_products()
            for product in mock_products:
                if product["id"] == product_id:
                    return product
            return {}
            
        endpoint = f"{self.base_url}/product/get"
        params = {
            "api_key": self.api_key,
            "account_id": self.account_id,
            "product_id": product_id
        }
        
        try:
            response = requests.get(endpoint, params=params)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error fetching product details: {str(e)}")
            return {}
    
    def get_affiliate_link(self, product_id):
        """Generate an affiliate link for a product."""
        if product_id.startswith("mock"):
            return f"https://warriorplus.com/o2/a/youraffid/{product_id}"
            
        endpoint = f"{self.base_url}/affiliate/get_link"
        params = {
            "api_key": self.api_key,
            "account_id": self.account_id,
            "product_id": product_id
        }
        
        try:
            response = requests.get(endpoint, params=params)
            response.raise_for_status()
            return response.json().get("affiliate_link", "")
        except Exception as e:
            logger.error(f"Error generating affiliate link: {str(e)}")
            return f"https://warriorplus.com/o2/a/youraffid/{product_id}"
    
    def generate_video_script(self, product_id):
        """Generate a high-converting video script for products with good ROI."""
        product = self.get_product_details(product_id)
        if not product:
            return ""
        
        # Extract key details
        name = product.get("name", "This amazing product")
        description = product.get("description", "")
        price = product.get("price", "$XX")
        benefits = product.get("benefits", "").split("\n") if product.get("benefits") else []
        
        # Fallback benefits if not available from API
        if not benefits or len(benefits) < 3:
            benefits = [
                "Save time and increase your productivity",
                "Generate more income with less effort",
                "Gain an unfair advantage over your competition",
                "Access proven methods used by top earners",
                "Eliminate costly trial and error in your business"
            ]
            # Take just 3 random benefits
            random.shuffle(benefits)
            benefits = benefits[:3]
        
        # Create a high-converting template with scarcity & social proof
        script = f"""
        Are you tired of struggling to see results? Look no further!
        
        TOP MARKETERS ARE RAVING about {name}!
        
        This EXCLUSIVE OPPORTUNITY gives you:
        
        {benefits[0]}
        {benefits[1]}
        {benefits[2]}
        
        {description[:100]}...
        
        For ONLY {price} - that's an INCREDIBLE value that won't last long!
        
        WARNING: This special offer is EXTREMELY LIMITED. Click the link in my bio NOW!
        
        Don't wait - those who act quickly are already seeing AMAZING RESULTS!
        """
        
        return script.strip()


class VideoGenerator:
    """Handles AI video generation optimized for high-converting marketing videos."""
    
    def __init__(self, config):
        self.provider = config["video_ai"]["provider"]
        self.api_key = config["video_ai"]["api_key"]
        self.output_dir = config["output_dir"]
    
    def generate_video(self, script, title, product_info=None):
        """
        Generate a high-quality marketing video using AI service.
        For PyDroid3 testing, this returns a mock video path.
        """
        logger.info(f"Generating high-converting video with {self.provider}: {title}")
        
        # For PyDroid3 testing, we'll simulate video generation
        # In a real implementation, you would call the actual API
        
        try:
            # Simulate API call and processing time
            print(f"Generating video: {title}")
            print("This would normally call the Synthesia API")
            print("Script preview: " + script[:100] + "...")
            
            # Simulate processing time
            for i in range(5):
                print(f"Processing video... {i+1}/5")
                time.sleep(1)
            
            # Create a mock video file (just a text file for testing)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            video_filename = f"{title.replace(' ', '_')}_{timestamp}.txt"
            video_path = os.path.join(self.output_dir, video_filename)
            
            with open(video_path, 'w') as f:
                f.write(f"Mock video for: {title}\n\nScript:\n{script}")
            
            logger.info(f"Mock video created at {video_path}")
            return video_path
            
        except Exception as e:
            logger.error(f"Error generating video: {str(e)}")
            notify_user("Video Generation Failed", str(e))
            return None


class InstagramSimulator:
    """Simulates Instagram posting for PyDroid3 testing."""
    
    def __init__(self, config):
        self.username = config["instagram"]["borggump"]
        self.password = config["instagram"]["hpgoia892!!!"]
    
    def post_video(self, video_path, caption):
        """
        Simulate posting to Instagram for testing purposes.
        """
        if not os.path.exists(video_path):
            logger.error(f"Video file not found: {video_path}")
            return False
        
        logger.info(f"Simulating Instagram post: {os.path.basename(video_path)}")
        
        try:
            print("\n" + "=" * 50)
            print("INSTAGRAM POST SIMULATION")
            print("=" * 50)
            print(f"Account: {self.username}")
            print(f"Video: {os.path.basename(video_path)}")
            print("\nCaption:")
            print("-" * 40)
            print(caption)
            print("-" * 40)
            print("\nThis would normally post to Instagram")
            print("=" * 50 + "\n")
            
            # Log the post details
            post_id = f"mock_post_{int(time.time())}"
            logger.info(f"Mock Instagram post created with ID: {post_id}")
            
            notify_user("Instagram Post Simulated", 
                       f"Video would be posted to Instagram as @{self.username}")
            return True
            
        except Exception as e:
            logger.error(f"Error in Instagram simulation: {str(e)}")
            notify_user("Instagram Post Failed", str(e))
            return False


class RandomScheduler:
    """Manages intelligent random scheduling of posts for maximum engagement."""
    
    def __init__(self, config):
        self.min_hours = config["scheduling"]["min_hours_between_posts"]
        self.max_hours = config["scheduling"]["max_hours_between_posts"]
        self.allowed_hours = config["scheduling"]["posting_hours"]
        self.allowed_days = config["scheduling"]["days_of_week"]
        
        # Instagram optimal posting times
        self.peak_hours = {
            0: [12, 18, 21],  # Monday: 12pm, 6pm, 9pm
            1: [10, 13, 19],  # Tuesday: 10am, 1pm, 7pm
            2: [11, 15, 19],  # Wednesday: 11am, 3pm, 7pm
            3: [11, 15, 20],  # Thursday: 11am, 3pm, 8pm
            4: [10, 14, 21],  # Friday: 10am, 2pm, 9pm
            5: [11, 15, 20],  # Saturday: 11am, 3pm, 8pm
            6: [10, 14, 19]   # Sunday: 10am, 2pm, 7pm
        }
    
    def get_next_schedule_time(self):
        """Calculate the next posting time using strategic randomization for optimal engagement."""
        # Get random hours between min and max for basic interval
        hours_from_now = random.randint(self.min_hours, self.max_hours)
        
        # Calculate initial target time
        now = datetime.now()
        target_time = now + timedelta(hours=hours_from_now)
        
        # Determine if we should try to hit a peak engagement time
        # 70% chance to target peak hours for better engagement
        target_peak_time = random.random() < 0.7
        
        if target_peak_time:
            # Find the next available peak day
            for days_ahead in range(7):  # Look up to a week ahead
                check_day = (now + timedelta(days=days_ahead)).weekday()
                
                if check_day in self.allowed_days and self.peak_hours.get(check_day):
                    # Find peak hours that are still in the future
                    future_peak_hours = []
                    check_date = (now + timedelta(days=days_ahead)).date()
                    
                    for peak_hour in self.peak_hours[check_day]:
                        peak_time = datetime.combine(check_date, datetime.min.time()).replace(hour=peak_hour)
                        if peak_time > now and peak_hour in self.allowed_hours:
                            future_peak_hours.append(peak_hour)
                    
                    if future_peak_hours:
                        # Select a random peak hour for this day
                        selected_hour = random.choice(future_peak_hours)
                        target_time = datetime.combine(check_date, datetime.min.time()).replace(hour=selected_hour)
                        
                        # Add some randomness (1-15 minutes) to avoid looking too predictable
                        random_minutes = random.randint(1, 15)
                        target_time += timedelta(minutes=random_minutes)
                        break
        
        # Ensure it's within allowed constraints
        while (target_time.hour not in self.allowed_hours or 
               target_time.weekday() not in self.allowed_days):
            
            # If hour not allowed, move to next allowed hour
            if target_time.hour not in self.allowed_hours:
                next_hour = min([h for h in self.allowed_hours if h > target_time.hour], default=self.allowed_hours[0])
                
                if next_hour <= target_time.hour:  # Means we wrapped to next day
                    target_time = target_time.replace(hour=next_hour, day=target_time.day+1)
                else:
                    target_time = target_time.replace(hour=next_hour)
            
            # If day not allowed, move to next allowed day
            if target_time.weekday() not in self.allowed_days:
                days_to_add = 1
                while (target_time + timedelta(days=days_to_add)).weekday() not in self.allowed_days:
                    days_to_add += 1
                target_time = target_time + timedelta(days=days_to_add)
        
        return target_time
    
    def schedule_next_post(self, job_func):
        """Schedule the next post at a random time."""
        next_time = self.get_next_schedule_time()
        
        # Format for human-readable logging
        time_str = next_time.strftime("%Y-%m-%d %H:%M:%S")
        logger.info(f"Scheduled next post for: {time_str}")
        
        # For PyDroid3 testing, we'll just display the next scheduled time
        print(f"\nNEXT POST SCHEDULED: {time_str}")
        print(f"Time until next post: {(next_time - datetime.now()).total_seconds() / 60:.1f} minutes")
        
        # For PyDroid3 testing, we'll actually execute immediately with a short delay
        # In a real implementation with 'schedule', you would use:
        # schedule.clear()
        # schedule.every().day.at(next_time.strftime("%H:%M")).do(job_func)
        
        # Simulate a short delay for testing
        delay_seconds = 10
        print(f"For testing purposes, will execute in {delay_seconds} seconds instead")
        time.sleep(delay_seconds)
        job_func()


def create_and_post():
    """Main function to create and post content."""
    try:
        # Initialize components
        warrior = WarriorPlusManager(CONFIG)
        video_gen = VideoGenerator(CONFIG)
        insta = InstagramSimulator(CONFIG)  # Using simulator for PyDroid3
        scheduler = RandomScheduler(CONFIG)
        
        # 1. Get high-return products from Warrior Plus
        products = warrior.get_high_return_products(limit=10)
        if not products:
            logger.warning("No high-return products found")
            notify_user("No Products Found", "Could not find suitable products to promote")
            return False
        
        # 2. Select a product with weighted random selection (favoring higher returns)
        if len(products) > 1:
            # Create weights based on return score or default to equal weights
            weights = [p.get("return_score", 1) for p in products]
            # Normalize weights if any exist
            if sum(weights) > 0:
                weights = [w/sum(weights) for w in weights]
            else:
                weights = None
            product = random.choices(products, weights=weights, k=1)[0]
        else:
            product = products[0]
            
        product_id = product.get("id")
        product_name = product.get("name", "Product")
        
        # Log product details for tracking performance
        logger.info(f"Selected product: {product_name} (ID: {product_id})")
        print(f"Selected product: {product_name}")
        print(f"Return metrics - EPC: {product.get('epc', 'N/A')}, " + 
              f"Conversion: {product.get('conversion_rate', 'N/A')}%, " +
              f"Commission: ${product.get('commission_amount', 'N/A')}")
        
        # 3. Generate affiliate link
        affiliate_link = warrior.get_affiliate_link(product_id)
        
        # 4. Generate video script
        script = warrior.generate_video_script(product_id)
        if not script:
            logger.error("Failed to generate script")
            notify_user("Script Generation Failed", "Could not create video script")
            return False
        
        # 5. Generate video
        video_title = f"{product_name} Promo"
        video_path = video_gen.generate_video(script, video_title, product)
        if not video_path:
            logger.error("Failed to generate video")
            notify_user("Video Generation Failed", "Could not create video")
            return False
        
        # 6. Create Instagram caption with hashtags and emojis
        hashtags = " ".join([
            "#makemoney", "#onlinebusiness", "#affiliate", "#warriorplus",
            "#digitalmarketing", "#onlinemarketing", "#passiveincome",
            "#makemoneyonline", "#workfromhome", "#sidehustle",
            "#affiliatemarketing", "#internetmarketing", "#entrepreneurship",
            "#onlineearning", "#marketingstrategy"
        ])
        
        caption = f"""
        🔥 NEW PRODUCT ALERT 🔥
        
        Just discovered {product_name}! This is a game-changer for anyone looking to improve their results.
        
        ✅ {product.get('description', '')[:80]}...
        
        💰 Limited time offer available now!
        
        👉 Click the link in my bio to learn more!
        
        {hashtags}
        """
        
        # 7. Post to Instagram
        success = insta.post_video(video_path, caption)
        if success:
            # 8. Schedule next post
            scheduler.schedule_next_post(create_and_post)
        
        return success
        
    except Exception as e:
        logger.error(f"Error in create_and_post: {str(e)}", exc_info=True)
        notify_user("Automation Error", str(e))
        
        # Schedule next post despite error
        scheduler = RandomScheduler(CONFIG)
        scheduler.schedule_next_post(create_and_post)
        return False


def main():
    """Main function to start the process."""
    print("\n" + "=" * 50)
    print("Warrior Plus to Instagram Automation".center(50))
    print("PyDroid3 Testing Version".center(50))
    print("=" * 50 + "\n")
    
    print("This script simulates the process of:")
    print("1. Finding high-return products on Warrior Plus")
    print("2. Generating AI marketing videos")
    print("3. Posting to Instagram on a random schedule")
    print("\nSince this is running in PyDroid3, we'll use simulations")
    print("instead of actual API calls.\n")
    
    # Check if API keys are configured
    if CONFIG["warrior_plus"]["api_key"] == "YOUR_WARRIOR_PLUS_API_KEY":
        print("WARNING: You're using mock data because API keys are not configured")
        print("For actual use, update the CONFIG section with your API keys\n")
    
    # Start the process
    create_and_post()


if __name__ == "__main__":
    main()
    