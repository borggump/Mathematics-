#!/usr/bin/env python3
"""
Android Mobile Automation for Warrior Plus Content to Instagram
with Random Posting Schedule

This script is designed to run on an Android device using Termux and Python.
It automates:
1. Pulling product info from Warrior Plus
2. Generating AI videos
3. Posting to Instagram with randomized scheduling

Requirements:
- Termux app installed on Android
- Python package in Termux (pkg install python)
- Termux:API add-on for Android automation
- Required Python packages: requests, schedule, random, pillow
"""

import os
import time
import random
import json
import requests
import schedule
import subprocess
from datetime import datetime, timedelta
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='/data/data/com.termux/files/home/warrior_instagram_automation.log'
)
logger = logging.getLogger(__name__)

# Configuration
CONFIG = {
    "warrior_plus": {
        "api_key": "YOUR_WARRIOR_PLUS_API_KEY",
        "account_id": "borggump",
    },
    "video_ai": {
        "provider": "synthesia",  # Options: "synthesia", "runway", "d-id", etc.
        "api_key": "YOUR_VIDEO_AI_API_KEY",
    },
    "instagram": {
        "username": "YOUR_INSTAGRAM_USERNAME",
        "password": "YOUR_INSTAGRAM_PASSWORD",  # Consider using a more secure method
    },
    "scheduling": {
        "min_hours_between_posts": 8,
        "max_hours_between_posts": 48,
        "posting_hours": range(9, 22),  # Only post between 9am and 10pm
        "days_of_week": [0, 1, 2, 3, 4, 5, 6],  # 0=Monday, 6=Sunday
    },
    "output_dir": "/data/data/com.termux/files/home/warrior_videos/"
}

# Ensure output directory exists
os.makedirs(CONFIG["output_dir"], exist_ok=True)


def send_termux_notification(title, message):
    """Send a notification to the Android device using Termux API."""
    try:
        subprocess.run(
            ["termux-notification", "--title", title, "--content", message],
            check=True
        )
        logger.info(f"Notification sent: {title} - {message}")
    except subprocess.SubprocessError as e:
        logger.error(f"Failed to send notification: {str(e)}")


class WarriorPlusManager:
    """Handles interactions with Warrior Plus marketplace."""
    
    def __init__(self, config):
        self.api_key = config["warrior_plus"]["api_key"]
        self.account_id = config["warrior_plus"]["account_id"]
        self.base_url = "https://warriorplus.com/api/v2"
    
    def get_trending_products(self, limit=5):
        """Fetch trending products from Warrior Plus marketplace."""
        endpoint = f"{self.base_url}/stats/trending_products"
        params = {
            "api_key": self.api_key,
            "account_id": self.account_id,
            "limit": limit
        }
        
        try:
            response = requests.get(endpoint, params=params)
            response.raise_for_status()
            return response.json().get("products", [])
        except Exception as e:
            logger.error(f"Error fetching trending products: {str(e)}")
            return []
    
    def get_product_details(self, product_id):
        """Get detailed information about a specific product."""
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
            return ""
    
    def generate_video_script(self, product_id):
        """Generate a video script based on product information."""
        product = self.get_product_details(product_id)
        if not product:
            return ""
        
        # Extract key details
        name = product.get("name", "This amazing product")
        description = product.get("description", "")
        price = product.get("price", "$XX")
        
        # Create a template for the video script
        script = f"""
        Looking for a way to level up your results?
        
        Introducing {name}!
        
        {description[:150]}...
        
        At just {price}, this is an incredible opportunity you don't want to miss.
        
        Check out the link in my bio to learn more and get instant access!
        
        Limited time offer - act now before it's gone!
        """
        
        return script.strip()


class VideoGenerator:
    """Handles AI video generation."""
    
    def __init__(self, config):
        self.provider = config["video_ai"]["provider"]
        self.api_key = config["video_ai"]["api_key"]
        self.output_dir = config["output_dir"]
    
    def generate_video(self, script, title):
        """
        Generate a video using AI service.
        
        Args:
            script: Text script for the video
            title: Title of the video
            
        Returns:
            str: Path to the generated video file
        """
        logger.info(f"Generating video with {self.provider}: {title}")
        
        if self.provider == "synthesia":
            return self._generate_with_synthesia(script, title)
        else:
            logger.error(f"Unsupported video provider: {self.provider}")
            return None
    
    def _generate_with_synthesia(self, script, title):
        """Generate video using Synthesia API."""
        api_url = "https://api.synthesia.io/v2/videos"
        
        # Randomly select an avatar/template for variety
        templates = ["realistic_male_1", "realistic_female_2", "casual_male_1"]
        selected_template = random.choice(templates)
        
        payload = {
            "title": title,
            "description": f"Auto-generated: {title}",
            "visibility": "private",
            "template": selected_template,
            "input": [{"scriptText": script}]
        }
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        try:
            # Create the video
            response = requests.post(api_url, json=payload, headers=headers)
            response.raise_for_status()
            video_id = response.json()["id"]
            
            # Poll until video is ready
            video_url = None
            max_attempts = 30
            attempts = 0
            
            while not video_url and attempts < max_attempts:
                attempts += 1
                time.sleep(20)  # Check every 20 seconds
                
                status_response = requests.get(f"{api_url}/{video_id}", headers=headers)
                status_response.raise_for_status()
                status_data = status_response.json()
                
                if status_data["status"] == "complete":
                    video_url = status_data["download"]
                    break
                elif status_data["status"] == "failed":
                    raise Exception(f"Video generation failed: {status_data.get('message', 'Unknown error')}")
                
                logger.info(f"Video still processing... Attempt {attempts}/{max_attempts}")
            
            if not video_url:
                raise Exception("Video generation timed out")
            
            # Download the video
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            video_filename = f"{title.replace(' ', '_')}_{timestamp}.mp4"
            video_path = os.path.join(self.output_dir, video_filename)
            
            with requests.get(video_url, stream=True) as r:
                r.raise_for_status()
                with open(video_path, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)
            
            logger.info(f"Video downloaded to {video_path}")
            return video_path
            
        except Exception as e:
            logger.error(f"Error generating video: {str(e)}")
            send_termux_notification("Video Generation Failed", str(e))
            return None


class InstagramAutomation:
    """Handles Instagram posting using Android automation."""
    
    def __init__(self, config):
        self.username = config["instagram"]["username"]
        self.password = config["instagram"]["password"]
    
    def post_video(self, video_path, caption):
        """
        Post video to Instagram using Termux API for Android automation.
        
        This uses UI automation to navigate the Instagram app.
        Note: This approach is subject to breaking with Instagram UI changes.
        """
        if not os.path.exists(video_path):
            logger.error(f"Video file not found: {video_path}")
            return False
        
        logger.info(f"Preparing to post video to Instagram: {os.path.basename(video_path)}")
        
        try:
            # 1. Open Instagram app
            subprocess.run(["am", "start", "-n", "com.instagram.android/.activity.MainTabActivity"], check=True)
            time.sleep(5)  # Wait for app to load
            
            # 2. Tap the "+" button to create new post
            subprocess.run(["termux-touch", "540 1800"], check=True)  # Adjust coordinates for your device
            time.sleep(2)
            
            # 3. Select "Video" option
            subprocess.run(["termux-touch", "540 1600"], check=True)  # Adjust coordinates for your device
            time.sleep(2)
            
            # 4. Navigate to the video file
            # Note: This is simplified. You may need to implement more robust file selection
            subprocess.run(["termux-storage-get", video_path], check=True)
            time.sleep(3)
            
            # 5. Next button
            subprocess.run(["termux-touch", "980 140"], check=True)  # Adjust coordinates for your device
            time.sleep(2)
            
            # 6. Skip filters (next button again)
            subprocess.run(["termux-touch", "980 140"], check=True)  # Adjust coordinates for your device
            time.sleep(2)
            
            # 7. Enter caption
            subprocess.run(["termux-clipboard-set", caption], check=True)
            subprocess.run(["termux-touch", "540 300"], check=True)  # Tap caption field
            time.sleep(1)
            subprocess.run(["termux-touch", "300 300", "--hold"], check=True)  # Long press for paste menu
            time.sleep(1)
            subprocess.run(["termux-touch", "300 400"], check=True)  # Tap "Paste" option
            time.sleep(2)
            
            # 8. Share button
            subprocess.run(["termux-touch", "980 140"], check=True)  # Adjust coordinates for your device
            time.sleep(5)
            
            logger.info("Instagram post initiated successfully")
            send_termux_notification("Instagram Post", "Video successfully posted to Instagram")
            return True
            
        except subprocess.SubprocessError as e:
            logger.error(f"Error posting to Instagram: {str(e)}")
            send_termux_notification("Instagram Post Failed", str(e))
            return False


class RandomScheduler:
    """Manages random scheduling of posts."""
    
    def __init__(self, config):
        self.min_hours = config["scheduling"]["min_hours_between_posts"]
        self.max_hours = config["scheduling"]["max_hours_between_posts"]
        self.allowed_hours = config["scheduling"]["posting_hours"]
        self.allowed_days = config["scheduling"]["days_of_week"]
    
    def get_next_schedule_time(self):
        """Calculate the next random posting time within constraints."""
        # Get random hours between min and max
        hours_from_now = random.randint(self.min_hours, self.max_hours)
        
        # Calculate target time
        now = datetime.now()
        target_time = now + timedelta(hours=hours_from_now)
        
        # Ensure it's within allowed posting hours
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
        send_termux_notification("Post Scheduled", f"Next post scheduled for {time_str}")
        
        # Schedule the job
        schedule.clear()
        schedule.every().day.at(next_time.strftime("%H:%M")).do(job_func)


def create_and_post():
    """Main function to create and post content."""
    try:
        # Initialize components
        warrior = WarriorPlusManager(CONFIG)
        video_gen = VideoGenerator(CONFIG)
        insta = InstagramAutomation(CONFIG)
        scheduler = RandomScheduler(CONFIG)
        
        # 1. Get trending products from Warrior Plus
        products = warrior.get_trending_products(limit=5)
        if not products:
            logger.error("No trending products found")
            return False
        
        # 2. Select a random product
        product = random.choice(products)
        product_id = product.get("id")
        product_name = product.get("name", "Product")
        
        # 3. Generate affiliate link
        affiliate_link = warrior.get_affiliate_link(product_id)
        
        # 4. Generate video script
        script = warrior.generate_video_script(product_id)
        if not script:
            logger.error("Failed to generate script")
            return False
        
        # 5. Generate video
        video_title = f"{product_name} Promo"
        video_path = video_gen.generate_video(script, video_title)
        if not video_path:
            logger.error("Failed to generate video")
            return False
        
        # 6. Create Instagram caption
        caption = f"""
        🔥 NEW PRODUCT ALERT 🔥
        
        Just discovered {product_name}! This is a game-changer for anyone looking to improve their results.
        
        💰 Limited time offer available now!
        
        👉 Click the link in my bio to learn more!
        
        #makemoney #onlinebusiness #affiliate #warriorplus
        """
        
        # 7. Post to Instagram
        success = insta.post_video(video_path, caption)
        if success:
            # 8. Schedule next post
            scheduler.schedule_next_post(create_and_post)
        
        return success
        
    except Exception as e:
        logger.error(f"Error in create_and_post: {str(e)}", exc_info=True)
        send_termux_notification("Automation Error", str(e))
        
        # Schedule next post despite error
        scheduler = RandomScheduler(CONFIG)
        scheduler.schedule_next_post(create_and_post)
        return False


def run_scheduler():
    """Run the scheduler loop."""
    # Initial schedule
    scheduler = RandomScheduler(CONFIG)
    scheduler.schedule_next_post(create_and_post)
    
    # Keep checking the schedule
    while True:
        schedule.run_pending()
        time.sleep(60)  # Check every minute


if __name__ == "__main__":
    # Send startup notification
    send_termux_notification(
        "Automation Started", 
        "Warrior Plus to Instagram automation is now running"
    )
    
    # Initiate the first post immediately or schedule it
    start_immediately = True
    
    if start_immediately:
        create_and_post()
    else:
        scheduler = RandomScheduler(CONFIG)
        scheduler.schedule_next_post(create_and_post)
    
    # Run the continuous scheduler
    run_scheduler()