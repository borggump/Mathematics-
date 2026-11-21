#!/usr/bin/env python3
"""
Automated AI Video Generation and Instagram Publishing Workflow

This script demonstrates a workflow to:
1. Generate video content using AI tools
2. Post the generated content to Instagram automatically
3. (Optional) Interface with Warrior Plus if needed for product promotion

Requirements:
- Python 3.8+
- API access to video generation service (e.g., Runway ML, Synthesia, D-ID)
- Instagram Graph API access
- (Optional) Warrior Plus API access if applicable

Note: You'll need to add your own API keys and customize the workflow for your specific needs.
"""

import os
import time
import requests
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler("video_automation.log"), logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Configuration - Replace with your actual API keys and settings
CONFIG = {
    "video_ai": {
        "provider": "synthesia",  # Options: "synthesia", "runway", "d-id", etc.
        "api_key": "YOUR_VIDEO_AI_API_KEY",
        "template_id": "YOUR_TEMPLATE_ID",  # If applicable
    },
    "instagram": {
        "access_token": "YOUR_INSTAGRAM_ACCESS_TOKEN",
        "user_id": "YOUR_INSTAGRAM_BUSINESS_ACCOUNT_ID",
    },
    "warrior_plus": {  # If applicable
        "api_key": "YOUR_WARRIOR_PLUS_API_KEY",
        "account_id": "YOUR_WARRIOR_PLUS_ACCOUNT_ID",
    },
    "output_dir": "generated_videos/",
}

# Ensure output directory exists
os.makedirs(CONFIG["output_dir"], exist_ok=True)


class VideoGenerator:
    """Handles AI video generation using various services."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.provider = config["video_ai"]["provider"]
        self.api_key = config["video_ai"]["api_key"]
        
    def generate_video(self, script: str, title: str) -> str:
        """
        Generate a video using the configured AI service.
        
        Args:
            script: The text script for the video
            title: The title of the video
            
        Returns:
            str: Path to the generated video file
        """
        logger.info(f"Generating video with {self.provider}: {title}")
        
        if self.provider == "synthesia":
            return self._generate_with_synthesia(script, title)
        elif self.provider == "runway":
            return self._generate_with_runway(script, title)
        elif self.provider == "d-id":
            return self._generate_with_did(script, title)
        else:
            raise ValueError(f"Unsupported video AI provider: {self.provider}")
    
    def _generate_with_synthesia(self, script: str, title: str) -> str:
        """Generate video using Synthesia API."""
        # This is a simplified example - actual implementation would use Synthesia's API
        api_url = "https://api.synthesia.io/v2/videos"
        
        payload = {
            "title": title,
            "description": f"Auto-generated video: {title}",
            "visibility": "public",
            "template": self.config["video_ai"]["template_id"],
            "input": [{"scriptText": script}]
        }
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # Create the video
        response = requests.post(api_url, json=payload, headers=headers)
        response.raise_for_status()
        video_id = response.json()["id"]
        
        # Poll until video is ready
        video_url = None
        while not video_url:
            time.sleep(10)  # Check every 10 seconds
            status_response = requests.get(f"{api_url}/{video_id}", headers=headers)
            status_response.raise_for_status()
            status_data = status_response.json()
            
            if status_data["status"] == "complete":
                video_url = status_data["download"]
                break
            elif status_data["status"] == "failed":
                raise Exception(f"Video generation failed: {status_data.get('message', 'Unknown error')}")
        
        # Download the video
        video_path = os.path.join(CONFIG["output_dir"], f"{title.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4")
        with requests.get(video_url, stream=True) as r:
            r.raise_for_status()
            with open(video_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
                    
        logger.info(f"Video downloaded to {video_path}")
        return video_path
    
    def _generate_with_runway(self, script: str, title: str) -> str:
        """Generate video using Runway ML API."""
        # Implementation for Runway would go here
        # This is a placeholder
        logger.info("Runway implementation not completed yet")
        return f"{CONFIG['output_dir']}/sample_runway_video.mp4"
    
    def _generate_with_did(self, script: str, title: str) -> str:
        """Generate video using D-ID API."""
        # Implementation for D-ID would go here
        # This is a placeholder
        logger.info("D-ID implementation not completed yet")
        return f"{CONFIG['output_dir']}/sample_did_video.mp4"


class InstagramPublisher:
    """Handles publishing to Instagram."""
    
    def __init__(self, config: Dict[str, Any]):
        self.access_token = config["instagram"]["access_token"]
        self.user_id = config["instagram"]["user_id"]
        
    def publish_video(self, video_path: str, caption: str) -> str:
        """
        Publish a video to Instagram.
        
        Args:
            video_path: Path to the video file
            caption: Caption for the Instagram post
            
        Returns:
            str: Instagram post ID if successful
        """
        logger.info(f"Publishing video to Instagram: {os.path.basename(video_path)}")
        
        # Step 1: Create a container
        container_id = self._create_container(video_path, caption)
        
        # Step 2: Publish the container
        post_id = self._publish_container(container_id)
        
        logger.info(f"Successfully published to Instagram, post ID: {post_id}")
        return post_id
    
    def _create_container(self, video_path: str, caption: str) -> str:
        """Create an Instagram container for the video."""
        api_url = f"https://graph.facebook.com/v18.0/{self.user_id}/media"
        
        params = {
            "access_token": self.access_token,
            "media_type": "VIDEO",
            "video": open(video_path, "rb"),
            "caption": caption,
        }
        
        response = requests.post(api_url, data=params)
        response.raise_for_status()
        return response.json()["id"]
    
    def _publish_container(self, container_id: str) -> str:
        """Publish the container to Instagram."""
        api_url = f"https://graph.facebook.com/v18.0/{self.user_id}/media_publish"
        
        params = {
            "access_token": self.access_token,
            "creation_id": container_id,
        }
        
        response = requests.post(api_url, data=params)
        response.raise_for_status()
        return response.json()["id"]


class WarriorPlusIntegration:
    """Optional: Integration with Warrior Plus platform."""
    
    def __init__(self, config: Dict[str, Any]):
        self.api_key = config["warrior_plus"]["api_key"]
        self.account_id = config["warrior_plus"]["account_id"]
        
    def get_product_info(self, product_id: str) -> Dict[str, Any]:
        """Get information about a product from Warrior Plus."""
        api_url = "https://warriorplus.com/api/v2/product/get"
        
        params = {
            "api_key": self.api_key,
            "account_id": self.account_id,
            "product_id": product_id,
        }
        
        response = requests.get(api_url, params=params)
        response.raise_for_status()
        return response.json()
    
    def get_affiliate_link(self, product_id: str) -> str:
        """Get your affiliate link for a product."""
        # Implementation would depend on Warrior Plus API specifications
        # This is a simplified example
        logger.info(f"Getting affiliate link for product {product_id}")
        return f"https://warriorplus.com/o2/a/youraffid/{product_id}"
    
    def generate_video_script(self, product_id: str) -> str:
        """Generate a video script based on product information."""
        product_info = self.get_product_info(product_id)
        
        # Simple template for a promotional video script
        script = f"""
        Are you looking for a way to {product_info['problem_statement']}?
        
        Introducing {product_info['name']} - the revolutionary solution that helps you {product_info['solution_statement']}.
        
        With {product_info['name']}, you'll be able to:
        - {product_info['benefit_1']}
        - {product_info['benefit_2']}
        - {product_info['benefit_3']}
        
        Don't wait! Click the link in the description to get started today!
        """
        
        return script.strip()


def main():
    """Main execution function."""
    try:
        # Initialize components
        video_generator = VideoGenerator(CONFIG)
        instagram_publisher = InstagramPublisher(CONFIG)
        
        # Optional: Initialize Warrior Plus integration if needed
        use_warrior_plus = "warrior_plus" in CONFIG and all(CONFIG["warrior_plus"].values())
        if use_warrior_plus:
            warrior_plus = WarriorPlusIntegration(CONFIG)
            
            # Get product info and generate script based on a product
            product_id = "YOUR_PRODUCT_ID"  # Replace with actual product ID
            script = warrior_plus.generate_video_script(product_id)
            affiliate_link = warrior_plus.get_affiliate_link(product_id)
            
            # Include affiliate link in the Instagram caption
            caption = f"Check out this amazing product! Click the link in my bio: {affiliate_link}"
        else:
            # Use a custom script if not using Warrior Plus
            script = """
            Hey there! This is an AI-generated video showcasing the power of automation.
            Imagine creating content like this automatically and publishing it to Instagram.
            Follow for more tech tips and automation ideas!
            """
            caption = "Automated content creation with AI #technology #automation #ai"
        
        # Generate the video
        video_title = f"AI Promo {datetime.now().strftime('%Y-%m-%d')}"
        video_path = video_generator.generate_video(script, video_title)
        
        # Publish to Instagram
        post_id = instagram_publisher.publish_video(video_path, caption)
        
        logger.info(f"Workflow completed successfully! Instagram Post ID: {post_id}")
        return True
        
    except Exception as e:
        logger.error(f"Error in automation workflow: {str(e)}", exc_info=True)
        return False


if __name__ == "__main__":
    main()