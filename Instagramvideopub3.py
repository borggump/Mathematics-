#!/usr/bin/env python3
"""
Affordable Warrior Plus to Instagram Automation

This script provides a cost-effective solution to:
1. Find profitable products on Warrior Plus
2. Create affordable AI videos using free/low-cost options
3. Post to Instagram on a randomized schedule

Key Features:
- Uses free/low-cost AI tools instead of expensive services like Synthesia
- Works on standard Python environments including mobile
- Optimized for low resource usage
- Includes fallbacks for API limitations
"""

import os
import time
import random
import json
import requests
import base64
from datetime import datetime, timedelta
import logging
import subprocess
from PIL import Image, ImageDraw, ImageFont
import textwrap
import io
import re

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='warrior_instagram_automation.log'
)
logger = logging.getLogger(__name__)

# Configuration
CONFIG = {
    "warrior_plus": {
        "api_key": "0102d96ea53b182e31ea534948eb89b",
        "account_id": "borggump",
    },
    "video_creation": {
        # Choose your preferred low-cost video creation method:
        # "slideshow" - Creates a slideshow video from text and images
        # "kapwing" - Uses Kapwing's affordable API
        # "invideo" - Uses InVideo's reasonably priced API
        # "canva" - Uses Canva's API for video creation
        "method": "slideshow",
        
        # API key only needed for non-slideshow methods
        "api_key": "DRsu-sHnUxKgmCjjV2dmj",
        
        # Slideshow settings (only used if method is "slideshow")
        "slideshow": {
            "duration": 15,  # seconds per slide
            "transition": "fade",  # fade, slide, etc.
            "text_color": "#FFFFFF",
            "background_color": "#000080",  # Navy blue
            "font_size": 40,
            "total_duration": 60,  # seconds
            "resolution": (1080, 1920),  # Instagram-friendly portrait (9:16)
        },
        
        # Stock image search (used to find relevant background images)
        "image_search": {
            "use_pexels": True,  # Free stock images
            "pexels_api_key": "TVOLGbiydvejt5Xc43mJjxzt3FyZbE7UWJD6MGNUB9HZ3MtlPmJK0LoQ",  # Get a free API key from Pexels
        }
    },
    "instagram": {
        "username": "borggump",
        "password": "hpgoia892!!!",
        
        # Method options:
        # "instagrapi" - Free open-source Instagram API library
        # "playwright" - Browser automation (more reliable but slower)
        "method": "instagrapi",
    },
    "scheduling": {
        "min_hours_between_posts": 12,
        "max_hours_between_posts": 72,
        "posting_hours": range(8, 23),  # 8am to 10pm
        "days_of_week": [0, 1, 2, 3, 4, 5, 6],  # All days
    },
    "output_dir": "warrior_videos"
}

# Ensure output directory exists
os.makedirs(CONFIG["output_dir"], exist_ok=True)


def notify_user(title, message):
    """Display notification to user."""
    print(f"\n=== {title} ===")
    print(message)
    print("=" * (len(title) + 8))
    logger.info(f"Notification: {title} - {message}")


class WarriorPlusManager:
    """Handles interactions with Warrior Plus marketplace."""
    
    def __init__(self, config):
        self.api_key = config["warrior_plus"]["api_key"]
        self.account_id = config["warrior_plus"]["account_id"]
        self.base_url = "https://warriorplus.com/api/v2"
    
    def get_high_return_products(self, limit=10):
        """Fetch high-converting products with good ROI from Warrior Plus marketplace."""
        endpoint = f"{self.base_url}/marketplace/search"
        params = {
            "api_key": self.api_key,
            "account_id": self.account_id,
            "limit": limit,
            "sort_by": "conversion_rate",  # Sort by highest conversion rate
            "min_epc": 0.5,  # Minimum earnings per click (good ROI indicator)
            "min_gravity": 5,  # Products with proven sales
            "status": "active"  # Only currently active offers
        }
        
        try:
            # For testing without API key, return mock data
            if self.api_key == "YOUR_WARRIOR_PLUS_API_KEY":
                logger.warning("Using mock data due to missing API key")
                return self.get_mock_products()
                
            response = requests.get(endpoint, params=params)
            response.raise_for_status()
            products = response.json().get("products", [])
            
            # Further filter products by additional metrics
            high_return_products = []
            for product in products:
                # Calculate a "return potential score"
                conv_rate = float(product.get("conversion_rate", 0))
                epc = float(product.get("epc", 0))
                commission = float(product.get("commission_amount", 0))
                
                # Simple scoring algorithm - adjust weights as needed
                return_score = (conv_rate * 0.4) + (epc * 0.4) + (commission * 0.2)
                
                product["return_score"] = return_score
                high_return_products.append(product)
            
            # Sort by our custom return score
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
    
    def generate_slideshow_content(self, product_id):
        """
        Generate content for slideshow-based video creation.
        Returns a list of slide content.
        """
        product = self.get_product_details(product_id)
        if not product:
            return []
        
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
            # Take 3-5 random benefits
            random.shuffle(benefits)
            benefits = benefits[:min(5, len(benefits))]
        
        # Create slides content
        slides = [
            {
                "title": "ATTENTION MARKETERS!",
                "subtitle": "Are you tired of struggling to see results?",
                "background_query": "frustrated business person",
                "duration": 3
            },
            {
                "title": f"Introducing {name}",
                "subtitle": "The solution you've been waiting for!",
                "background_query": "success celebration",
                "duration": 4
            }
        ]
        
        # Add benefits slides
        for i, benefit in enumerate(benefits):
            slides.append({
                "title": f"BENEFIT #{i+1}",
                "subtitle": benefit,
                "background_query": "business success",
                "duration": 3
            })
        
        # Add description slide
        slides.append({
            "title": "What is it?",
            "subtitle": description[:150] + "..." if len(description) > 150 else description,
            "background_query": "digital marketing",
            "duration": 4
        })
        
        # Add pricing slide
        slides.append({
            "title": f"SPECIAL OFFER: ONLY {price}",
            "subtitle": "Limited time offer - Act fast!",
            "background_query": "special offer deal",
            "duration": 3
        })
        
        # Add call to action slide
        slides.append({
            "title": "CLICK THE LINK IN BIO",
            "subtitle": "Start seeing results TODAY!",
            "background_query": "call to action button",
            "duration": 4
        })
        
        return slides


class AffordableVideoCreator:
    """Creates videos using affordable or free methods."""
    
    def __init__(self, config):
        self.config = config
        self.method = config["video_creation"]["method"]
        self.api_key = config["video_creation"]["api_key"]
        self.output_dir = config["output_dir"]
        self.slideshow_settings = config["video_creation"]["slideshow"]
        
        # Set up image search if configured
        self.use_image_search = config["video_creation"]["image_search"]["use_pexels"]
        self.pexels_api_key = config["video_creation"]["image_search"]["pexels_api_key"]
    
    def create_video(self, script, title, product_info=None, slides_content=None):
        """
        Create a video using the configured method.
        
        Args:
            script: Text script for the video
            title: Title of the video
            product_info: Optional product information
            slides_content: Optional pre-generated slides content
            
        Returns:
            str: Path to the generated video file
        """
        logger.info(f"Creating video with {self.method} method: {title}")
        
        try:
            if self.method == "slideshow":
                return self._create_slideshow_video(script, title, slides_content)
            elif self.method == "kapwing":
                return self._create_kapwing_video(script, title, product_info)
            elif self.method == "invideo":
                return self._create_invideo_video(script, title, product_info)
            elif self.method == "canva":
                return self._create_canva_video(script, title, product_info)
            else:
                logger.error(f"Unsupported video creation method: {self.method}")
                return None
        except Exception as e:
            logger.error(f"Error creating video: {str(e)}")
            notify_user("Video Creation Failed", str(e))
            return None
    
    def _create_slideshow_video(self, script, title, slides_content):
        """
        Create a slideshow video from text and background images.
        This is the most affordable method as it doesn't require expensive APIs.
        """
        logger.info(f"Creating slideshow video: {title}")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"{title.replace(' ', '_')}_{timestamp}.mp4"
        output_path = os.path.join(self.output_dir, output_filename)
        
        # Create temporary directory for frames
        import tempfile
        frames_dir = tempfile.mkdtemp()
        
        try:
            # If slides_content not provided, create simple slides from script
            if not slides_content:
                # Split script into paragraphs for slides
                paragraphs = [p.strip() for p in script.split('\n') if p.strip()]
                slides_content = []
                
                for i, paragraph in enumerate(paragraphs):
                    # Skip very short paragraphs
                    if len(paragraph) < 10:
                        continue
                        
                    # Create a title from the first few words
                    words = paragraph.split()
                    title_words = words[:min(5, len(words))]
                    title = " ".join(title_words).upper()
                    
                    # Rest of paragraph becomes subtitle
                    subtitle = paragraph
                    
                    # For longer paragraphs, just use the first part
                    if len(subtitle) > 150:
                        subtitle = subtitle[:147] + "..."
                    
                    slides_content.append({
                        "title": title,
                        "subtitle": subtitle,
                        "background_query": "business marketing",
                        "duration": 5
                    })
            
            # Limit number of slides based on total duration
            total_slide_duration = sum(slide.get("duration", 3) for slide in slides_content)
            target_duration = self.slideshow_settings["total_duration"]
            
            if total_slide_duration > target_duration:
                # Scale durations proportionally
                scale_factor = target_duration / total_slide_duration
                for slide in slides_content:
                    slide["duration"] = max(2, int(slide.get("duration", 3) * scale_factor))
            
            # Generate frames for each slide
            frame_paths = []
            frame_durations = []
            frame_count = 0
            
            for i, slide in enumerate(slides_content):
                # Create image for this slide
                slide_img = self._create_slide_image(
                    slide.get("title", ""),
                    slide.get("subtitle", ""),
                    slide.get("background_query", "business")
                )
                
                # Save frames for this slide (1 frame per second)
                duration = slide.get("duration", 3)
                frame_durations.append(duration)
                
                for j in range(duration):
                    frame_path = os.path.join(frames_dir, f"frame_{frame_count:04d}.jpg")
                    slide_img.save(frame_path, "JPEG", quality=95)
                    frame_paths.append(frame_path)
                    frame_count += 1
            
            # Use ffmpeg to create video from frames
            self._frames_to_video(frame_paths, output_path)
            
            logger.info(f"Created slideshow video: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error creating slideshow: {str(e)}")
            
            # Fallback: Create a static image with text as a "video"
            try:
                logger.info("Attempting fallback to static image video")
                
                # Create a single slide with key information
                img = self._create_slide_image(
                    title,
                    script[:200] + "..." if len(script) > 200 else script,
                    "business marketing"
                )
                
                # Save image
                image_path = os.path.join(self.output_dir, f"{title.replace(' ', '_')}_{timestamp}.jpg")
                img.save(image_path, "JPEG", quality=95)
                
                # Create a static video from the image
                self._image_to_video(image_path, output_path, duration=30)
                
                logger.info(f"Created fallback static video: {output_path}")
                return output_path
                
            except Exception as fallback_error:
                logger.error(f"Fallback also failed: {str(fallback_error)}")
                return None
    
    def _create_slide_image(self, title, subtitle, background_query):
        """Create an image for a slide with title and subtitle."""
        width, height = self.slideshow_settings["resolution"]
        
        try:
            # Try to get a background image if image search is enabled
            background_img = None
            if self.use_image_search and self.pexels_api_key != "YOUR_PEXELS_API_KEY":
                background_img = self._get_background_image(background_query, width, height)
            
            # Create a new image if no background was found
            if background_img is None:
                background_img = Image.new("RGB", (width, height), self.slideshow_settings["background_color"])
            
            # Add a semi-transparent overlay to ensure text is readable
            overlay = Image.new("RGBA", (width, height), (0, 0, 0, 128))
            background_img = background_img.convert("RGBA")
            background_img = Image.alpha_composite(background_img, overlay).convert("RGB")
            
            # Set up drawing context
            draw = ImageDraw.Draw(background_img)
            
            # Try to load a font, fall back to default if not available
            try:
                title_font_size = self.slideshow_settings["font_size"]
                subtitle_font_size = int(title_font_size * 0.7)
                
                # Try a few common fonts that might be available
                font_names = ["Arial.ttf", "Verdana.ttf", "DejaVuSans.ttf", "FreeSans.ttf", "NotoSans-Regular.ttf"]
                title_font = None
                subtitle_font = None
                
                for font_name in font_names:
                    try:
                        title_font = ImageFont.truetype(font_name, title_font_size)
                        subtitle_font = ImageFont.truetype(font_name, subtitle_font_size)
                        break
                    except (OSError, IOError):
                        continue
                
                # If no font could be loaded, use default
                if title_font is None:
                    title_font = ImageFont.load_default()
                    subtitle_font = ImageFont.load_default()
                    
            except Exception:
                # Fall back to default font if anything goes wrong
                title_font = ImageFont.load_default()
                subtitle_font = ImageFont.load_default()
            
            # Draw title text
            title_color = self.slideshow_settings["text_color"]
            
            # Wrap text to fit on image
            wrapped_title = textwrap.fill(title, width=30)
            title_bbox = draw.textbbox((0, 0), wrapped_title, font=title_font)
            title_width = title_bbox[2] - title_bbox[0]
            title_height = title_bbox[3] - title_bbox[1]
            
            title_position = ((width - title_width) // 2, height // 4 - title_height // 2)
            draw.text(title_position, wrapped_title, fill=title_color, font=title_font)
            
            # Draw subtitle text
            wrapped_subtitle = textwrap.fill(subtitle, width=40)
            subtitle_bbox = draw.textbbox((0, 0), wrapped_subtitle, font=subtitle_font)
            subtitle_width = subtitle_bbox[2] - subtitle_bbox[0]
            subtitle_height = subtitle_bbox[3] - subtitle_bbox[1]
            
            subtitle_position = ((width - subtitle_width) // 2, height // 2 - subtitle_height // 2)
            draw.text(subtitle_position, wrapped_subtitle, fill=title_color, font=subtitle_font)
            
            return background_img
            
        except Exception as e:
            logger.error(f"Error creating slide image: {str(e)}")
            
            # Create a simple fallback image
            img = Image.new("RGB", (width, height), self.slideshow_settings["background_color"])
            draw = ImageDraw.Draw(img)
            draw.text((50, 50), title, fill=self.slideshow_settings["text_color"])
            draw.text((50, 100), subtitle, fill=self.slideshow_settings["text_color"])
            return img
    
    def _get_background_image(self, query, width, height):
        """Get a background image from Pexels API."""
        try:
            headers = {
                "Authorization": self.pexels_api_key
            }
            
            # Search for images
            search_url = f"https://api.pexels.com/v1/search?query={query}&per_page=1&orientation=portrait"
            response = requests.get(search_url, headers=headers)
            response.raise_for_status()
            
            data = response.json()
            if "photos" in data and len(data["photos"]) > 0:
                photo = data["photos"][0]
                
                # Get the best size image
                if "src" in photo:
                    # Use the largest available size that's not too large
                    img_url = photo["src"].get("large2x") or photo["src"].get("large") or photo["src"].get("original")
                    
                    if img_url:
                        # Download and resize image
                        img_response = requests.get(img_url)
                        img_response.raise_for_status()
                        
                        img = Image.open(io.BytesIO(img_response.content))
                        img = img.resize((width, height), Image.LANCZOS)
                        return img
            
            return None
            
        except Exception as e:
            logger.error(f"Error fetching background image: {str(e)}")
            return None
    
    def _frames_to_video(self, frame_paths, output_path):
        """Convert a sequence of image frames to a video using ffmpeg."""
        if not frame_paths:
            raise ValueError("No frames provided")
        
        try:
            # Check if ffmpeg is available
            try:
                subprocess.run(["ffmpeg", "-version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
            except (subprocess.SubprocessError, FileNotFoundError):
                logger.warning("ffmpeg not found, falling back to alternative method")
                return self._frames_to_video_alternative(frame_paths, output_path)
            
            # Create video with ffmpeg
            frame_pattern = os.path.join(os.path.dirname(frame_paths[0]), "frame_%04d.jpg")
            
            # Run ffmpeg command
            cmd = [
                "ffmpeg",
                "-y",  # Overwrite output file if it exists
                "-framerate", "1",  # 1 frame per second
                "-i", frame_pattern,
                "-c:v", "libx264",
                "-pix_fmt", "yuv420p",
                "-preset", "medium",
                "-crf", "23",  # Quality setting (lower is better)
                output_path
            ]
            
            subprocess.run(cmd, check=True)
            
            return True
            
        except Exception as e:
            logger.error(f"Error creating video with ffmpeg: {str(e)}")
            
            # Try alternative method
            return self._frames_to_video_alternative(frame_paths, output_path)
    
    def _frames_to_video_alternative(self, frame_paths, output_path):
        """
        Alternative method to create a video when ffmpeg is not available.
        This is a simplified method that might not produce optimal results.
        """
        try:
            # If imageio is available, use it
            import imageio
            
            with imageio.get_writer(output_path, fps=1) as writer:
                for frame_path in frame_paths:
                    writer.append_data(imageio.imread(frame_path))
            
            return True
            
        except ImportError:
            logger.error("imageio not available for video creation")
            
            # If all else fails, just copy the first frame as a static image
            import shutil
            if frame_paths:
                shutil.copy(frame_paths[0], output_path.replace(".mp4", ".jpg"))
                logger.warning(f"Created static image instead of video: {output_path.replace('.mp4', '.jpg')}")
                return False
            
            return False
    
    def _image_to_video(self, image_path, output_path, duration=10):
        """Convert a single image to a video of specified duration."""
        try:
            # Check if ffmpeg is available
            try:
                subprocess.run(["ffmpeg", "-version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
            except (subprocess.SubprocessError, FileNotFoundError):
                logger.warning("ffmpeg not found, falling back to alternative method")
                return False
            
            # Create video with ffmpeg
            cmd = [
                "ffmpeg",
                "-y",  # Overwrite output file if it exists
                "-loop", "1",  # Loop the input
                "-i", image_path,  # Input image
                "-c:v", "libx264",
                "-t", str(duration),  # Duration in seconds
                "-pix_fmt", "yuv420p",
                "-vf", "scale=trunc(iw/2)*2:trunc(ih/2)*2",  # Ensure dimensions are even
                output_path
            ]
            
            subprocess.run(cmd, check=True)
            return True
            
        except Exception as e:
            logger.error(f"Error creating video from image: {str(e)}")
            return False
    
    def _create_kapwing_video(self, script, title, product_info):
        """Create video using Kapwing API (affordable option)."""
        logger.warning("Kapwing API implementation not included - using slideshow fallback")
        return self._create_slideshow_video(script, title, None)
    
    def _create_invideo_video(self, script, title, product_info):
        """Create video using InVideo API (affordable option)."""
        logger.warning("InVideo API implementation not included - using slideshow fallback")
        return self._create_slideshow_video(script, title, None)
    
    def _create_canva_video(self, script, title, product_info):
        """Create video using Canva API (affordable option)."""
        logger.warning("Canva API implementation not included - using slideshow fallback")
        return self._create_slideshow_video(script, title, None)


class InstagramPublisher:
    """Handles Instagram posting using affordable methods."""
    
    def __init__(self, config):
        self.config = config
        self.username = config["instagram"]["username"]
        self.password = config["instagram"]["password"]
        self.method = config["instagram"]["method"]
    
    def post_video(self, video_path, caption):
        """
        Post video to Instagram using configured method.
        
        Args:
            video_path: Path to the video file
            caption: Caption for the Instagram post
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not os.path.exists(video_path):
            logger.error(f"Video file not found: {video_path}")
            return False
        
        logger.info(f"Posting to Instagram: {os.path.basename(video_path)}")
        
        try:
            if self.metho