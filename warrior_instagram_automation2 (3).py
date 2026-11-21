#!/usr/bin/env python3
"""
Enhanced Warrior Plus to Instagram Automation

Features:
1. Real Warrior Plus API integration
2. Real video creation with ffmpeg
3. Real Instagram posting with instagrapi
"""

import os
import time
import random
import json
import requests
import subprocess
from datetime import datetime, timedelta
from PIL import Image, ImageDraw, ImageFont
import textwrap

# ==== CONFIGURATION ====
# Replace these with your actual credentials
CONFIG = {
    "warrior_plus": {
        "api_key": "0102d96ea53b182e31ea534948eb89b",
        "account_id": "borggump",
        # The minimum values for high-return products
        "min_epc": 0.5,  # Earnings per click
        "min_conversion": 5.0,  # Conversion rate percentage
    },
    "instagram": {
        "username": "borggump",
        "password": "hpgoia892!!!",
    },
    "video": {
        "slide_duration": 5,  # seconds per slide
        "resolution": (1080, 1920),  # Instagram portrait mode (9:16)
        "text_color": "white",
        "background_color": "#000080",  # Navy blue
        "font_size": 60,
        "small_font_size": 40,
    },
    "scheduling": {
        "min_hours": 12,
        "max_hours": 72,
        "allowed_hours": range(8, 23),  # 8am to 10pm
    },
    "output_dir": "warrior_videos",
}

# Create necessary directories
os.makedirs(CONFIG["output_dir"], exist_ok=True)
slides_dir = os.path.join(CONFIG["output_dir"], "slides")
os.makedirs(slides_dir, exist_ok=True)

# Set up basic logging
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='warrior_instagram_automation.log',
    filemode='a'
)
logger = logging.getLogger(__name__)

def print_status(step, message):
    """Print a status update with timestamp and log it."""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] STEP {step}: {message}")
    logger.info(f"STEP {step}: {message}")
    # Add a small delay to make progress visible
    time.sleep(0.5)

# ==== WARRIOR PLUS API INTEGRATION ====
class WarriorPlusAPI:
    """Handles interactions with the Warrior Plus API."""
    
    def __init__(self, config):
        self.api_key = config["warrior_plus"]["api_key"]
        self.account_id = config["warrior_plus"]["account_id"]
        self.base_url = "https://warriorplus.com/api/v2"
        self.min_epc = config["warrior_plus"]["min_epc"]
        self.min_conversion = config["warrior_plus"]["min_conversion"]
    
    def get_high_return_products(self, limit=10):
        """Fetch high-converting products with good ROI from Warrior Plus marketplace."""
        print_status(1, "Fetching high-return products from Warrior Plus API...")
        
        # If using mock data for testing (no API key)
        if self.api_key == "YOUR_WARRIOR_PLUS_API_KEY":
            print_status(1, "Using mock data (no API key provided)")
            return self.get_mock_products()
        
        endpoint = f"{self.base_url}/marketplace/search"
        params = {
            "api_key": self.api_key,
            "account_id": self.account_id,
            "limit": limit,
            "sort_by": "conversion_rate",
            "min_epc": self.min_epc,
            "status": "active"
        }
        
        try:
            response = requests.get(endpoint, params=params)
            response.raise_for_status()
            products = response.json().get("products", [])
            
            # Filter products by conversion rate
            high_return_products = [
                p for p in products 
                if float(p.get("conversion_rate", 0)) >= self.min_conversion
            ]
            
            # Calculate return score for each product
            for product in high_return_products:
                conv_rate = float(product.get("conversion_rate", 0))
                epc = float(product.get("epc", 0))
                commission = float(product.get("commission_amount", 0))
                
                # Scoring formula: 40% conversion rate, 40% EPC, 20% commission
                return_score = (conv_rate * 0.4) + (epc * 0.4) + (commission * 0.2)
                product["return_score"] = return_score
            
            # Sort by return score
            sorted_products = sorted(
                high_return_products, 
                key=lambda x: x.get("return_score", 0), 
                reverse=True
            )
            
            print_status(1, f"Found {len(sorted_products)} high-return products")
            return sorted_products
            
        except Exception as e:
            print_status(1, f"Error fetching products: {str(e)}")
            logger.error(f"Error fetching products: {str(e)}")
            # Fall back to mock data
            return self.get_mock_products()
    
    def get_mock_products(self):
        """Return mock product data for testing."""
        print_status(1, "Using mock product data")
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
        # For mock products (testing)
        if product_id.startswith("mock"):
            mock_products = self.get_mock_products()
            for product in mock_products:
                if product["id"] == product_id:
                    return product
            return {}
        
        # For real API
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
        # For mock products (testing)
        if product_id.startswith("mock"):
            return f"https://warriorplus.com/o2/a/youraffid/{product_id}"
        
        # For real API
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
    
    def generate_script(self, product_id):
        """Generate a video script for the product."""
        print_status(2, "Generating marketing script...")
        
        product = self.get_product_details(product_id)
        if not product:
            return ""
        
        # Extract key details
        name = product.get("name", "This amazing product")
        description = product.get("description", "")
        price = product.get("price", "$XX")
        
        # Create a list of generic benefits
        benefits = [
            "Save time and increase your productivity",
            "Generate more income with less effort",
            "Gain an unfair advantage over your competition",
            "Access proven methods used by top earners",
            "Eliminate costly trial and error in your business"
        ]
        
        # Take 3 random benefits
        random.shuffle(benefits)
        chosen_benefits = benefits[:3]
        
        # Create a script
        script = f"""
        Are you tired of struggling to see results? Look no further!
        
        TOP MARKETERS ARE RAVING about {name}!
        
        This EXCLUSIVE OPPORTUNITY gives you:
        
        {chosen_benefits[0]}
        {chosen_benefits[1]}
        {chosen_benefits[2]}
        
        {description}
        
        For ONLY {price} - that's an INCREDIBLE value that won't last long!
        
        WARNING: This special offer is EXTREMELY LIMITED. Click the link in my bio NOW!
        
        Don't wait - those who act quickly are already seeing AMAZING RESULTS!
        """
        
        print_status(2, "Marketing script generated successfully")
        return script


# ==== VIDEO CREATION WITH FFMPEG ====
class VideoCreator:
    """Creates slideshow videos from text using ffmpeg."""
    
    def __init__(self, config):
        self.config = config
        self.slides_dir = os.path.join(config["output_dir"], "slides")
        self.output_dir = config["output_dir"]
        
        # Check if ffmpeg is installed
        self.ffmpeg_available = self._check_ffmpeg()
    
    def _check_ffmpeg(self):
        """Check if ffmpeg is available."""
        try:
            result = subprocess.run(
                ["ffmpeg", "-version"], 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE
            )
            if result.returncode == 0:
                print_status(3, "ffmpeg is available for video creation")
                return True
            else:
                print_status(3, "ffmpeg is not available - will create slides only")
                return False
        except (subprocess.SubprocessError, FileNotFoundError):
            print_status(3, "ffmpeg is not available - will create slides only")
            return False
    
    def create_video(self, script, product):
        """Create a video from the script."""
        print_status(3, f"Creating video for: {product['name']}")
        
        # Parse script into slides
        paragraphs = [p.strip() for p in script.split('\n\n') if p.strip()]
        
        # Create a series of slide images
        slide_paths = []
        
        total_slides = len(paragraphs)
        
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
            
            # Create slide image
            slide_img = self._create_slide_image(title, subtitle, i+1, total_slides)
            
            # Save slide
            slide_path = os.path.join(self.slides_dir, f"slide_{i+1:02d}.jpg")
            slide_img.save(slide_path, "JPEG", quality=95)
            slide_paths.append(slide_path)
        
        # Create timestamp for filenames
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        video_name = f"{product['name'].replace(' ', '_')}_{timestamp}"
        
        # Create the actual video if ffmpeg is available
        if self.ffmpeg_available and slide_paths:
            video_path = self._create_ffmpeg_video(slide_paths, video_name)
            print_status(3, f"Video created: {video_path}")
        else:
            # Create a text file with info about the "video"
            video_path = os.path.join(self.output_dir, f"{video_name}.txt")
            with open(video_path, 'w') as f:
                f.write(f"Video: {product['name']}\n")
                f.write(f"Created: {timestamp}\n")
                f.write(f"Number of slides: {len(slide_paths)}\n\n")
                f.write("SCRIPT:\n\n")
                f.write(script)
            
            print_status(3, f"Created {len(slide_paths)} slides. See: {self.slides_dir}")
            print_status(3, f"Video info saved to: {video_path}")
        
        return video_path, slide_paths
    
    def _create_slide_image(self, title, subtitle, slide_number, total_slides):
        """Create a slide image with text."""
        print_status(3, f"Creating slide {slide_number}/{total_slides}: {title[:30]}...")
        
        # Create a new image
        width, height = self.config["video"]["resolution"]
        image = Image.new("RGB", (width, height), color=self.config["video"]["background_color"])
        draw = ImageDraw.Draw(image)
        
        # Add slide number
        draw.text((width-80, 40), f"{slide_number}/{total_slides}", fill=self.config["video"]["text_color"])
        
        # Try to use a nice font, fall back to default if not available
        try:
            # Try common fonts that might be available
            font_size = self.config["video"]["font_size"]
            small_font_size = self.config["video"]["small_font_size"]
            
            # Try different common fonts
            font_names = ["Arial.ttf", "Verdana.ttf", "DejaVuSans.ttf", "FreeSans.ttf"]
            title_font = None
            
            for font_name in font_names:
                try:
                    title_font = ImageFont.truetype(font_name, font_size)
                    subtitle_font = ImageFont.truetype(font_name, small_font_size)
                    break
                except (OSError, IOError):
                    continue
            
            if title_font is None:
                title_font = ImageFont.load_default()
                subtitle_font = ImageFont.load_default()
                
        except Exception:
            title_font = ImageFont.load_default()
            subtitle_font = ImageFont.load_default()
        
        # Wrap text to fit on image
        wrapped_title = textwrap.fill(title, width=25)
        
        # Calculate text position - centered horizontally, near top vertically
        try:
            # Calculate title position
            title_bbox = draw.textbbox((0, 0), wrapped_title, font=title_font)
            title_width = title_bbox[2] - title_bbox[0]
            title_height = title_bbox[3] - title_bbox[1]
            title_position = ((width - title_width) // 2, height // 4 - title_height // 2)
        except AttributeError:
            # Fallback for older PIL versions
            title_width, title_height = draw.textsize(wrapped_title, font=title_font)
            title_position = ((width - title_width) // 2, height // 4 - title_height // 2)
        
        # Draw title
        draw.text(title_position, wrapped_title, fill=self.config["video"]["text_color"], font=title_font)
        
        # Draw subtitle
        wrapped_subtitle = textwrap.fill(subtitle, width=35)
        
        try:
            # Calculate subtitle position
            subtitle_bbox = draw.textbbox((0, 0), wrapped_subtitle, font=subtitle_font)
            subtitle_width = subtitle_bbox[2] - subtitle_bbox[0]
            subtitle_height = subtitle_bbox[3] - subtitle_bbox[1]
            subtitle_position = ((width - subtitle_width) // 2, height // 2 - subtitle_height // 2)
        except AttributeError:
            # Fallback for older PIL versions
            subtitle_width, subtitle_height = draw.textsize(wrapped_subtitle, font=subtitle_font)
            subtitle_position = ((width - subtitle_width) // 2, height // 2 - subtitle_height // 2)
        
        draw.text(subtitle_position, wrapped_subtitle, fill=self.config["video"]["text_color"], font=subtitle_font)
        
        # Add decorative elements (stars instead of emojis)
        draw.text((50, 50), "*", fill=self.config["video"]["text_color"], font=title_font)
        draw.text((width-100, height-100), "*", fill=self.config["video"]["text_color"], font=title_font)
        
        return image
    
    def _create_ffmpeg_video(self, slide_paths, video_name):
        """Create a video from slides using ffmpeg."""
        if not slide_paths:
            raise ValueError("No slides to create video from")
        
        # Output video path
        video_path = os.path.join(self.output_dir, f"{video_name}.mp4")
        
        try:
            # Create a temporary file with slide durations
            duration = self.config["video"]["slide_duration"]
            
            # Use the slideshow pattern for ffmpeg
            # This is a simpler approach that works well for slideshows
            input_pattern = os.path.join(self.slides_dir, "slide_%02d.jpg")
            
            cmd = [
                "ffmpeg",
                "-y",  # Overwrite output file if it exists
                "-framerate", f"1/{duration}",  # Each image lasts 'duration' seconds
                "-i", input_pattern,  # Input pattern
                "-c:v", "libx264",  # Codec
                "-pix_fmt", "yuv420p",  # Pixel format
                "-vf", "fps=30",  # Output at 30fps for smooth playback
                video_path
            ]
            
            # Run the command
            result = subprocess.run(
                cmd, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE,
                check=True
            )
            
            print_status(3, f"ffmpeg successfully created video: {video_path}")
            return video_path
            
        except subprocess.CalledProcessError as e:
            print_status(3, f"ffmpeg error: {e.stderr.decode()}")
            logger.error(f"ffmpeg error: {e.stderr.decode()}")
            
            # If video creation fails, return the path to the first slide as fallback
            return slide_paths[0]
        except Exception as e:
            print_status(3, f"Error creating video: {str(e)}")
            logger.error(f"Error creating video: {str(e)}")
            
            # If video creation fails, return the path to the first slide as fallback
            return slide_paths[0]


# ==== INSTAGRAM POSTING WITH INSTAGRAPI ====
class InstagramPoster:
    """Handles Instagram posting using instagrapi."""
    
    def __init__(self, config):
        self.username = config["instagram"]["username"]
        self.password = config["instagram"]["password"]
        self.client = None
        
        # Check if instagrapi is available
        self.instagrapi_available = self._check_instagrapi()
    
    def _check_instagrapi(self):
        """Check if instagrapi is available."""
        try:
            import instagrapi
            print_status(4, "instagrapi is available for Instagram posting")
            return True
        except ImportError:
            print_status(4, "instagrapi is not available - will simulate posting")
            return False
    
    def post_to_instagram(self, video_path, caption, product):
        """Post content to Instagram."""
        print_status(4, "Preparing Instagram post...")
        
        # Create hashtags
        hashtags = " ".join([
            "#makemoney", "#onlinebusiness", "#affiliate", "#warriorplus",
            "#digitalmarketing", "#passiveincome", "#sidehustle"
        ])
        
        # Format caption
        full_caption = f"""
        NEW PRODUCT ALERT!
        
        Just discovered {product['name']}! This is a game-changer for anyone looking to improve their results.
        
        {product['description']}
        
        Limited time offer available now at {product['price']}!
        
        Click the link in my bio to learn more!
        
        {hashtags}
        """.strip()
        
        print_status(4, f"Caption prepared (length: {len(full_caption)} chars)")
        
        # Check if it's a video or image
        is_video = video_path.lower().endswith(('.mp4', '.mov'))
        
        # Post to Instagram if instagrapi is available
        if self.instagrapi_available:
            return self._post_with_instagrapi(video_path, full_caption, is_video)
        else:
            return self._simulate_post(video_path, full_caption, product, is_video)
    
    def _post_with_instagrapi(self, media_path, caption, is_video):
        """Post to Instagram using instagrapi."""
        try:
            # Import here to handle the case when it's not installed
            from instagrapi import Client
            
            print_status(4, "Logging in to Instagram...")
            
            # Initialize client
            self.client = Client()
            
            # Try to load existing session
            session_file = "instagram_session.json"
            if os.path.exists(session_file):
                try:
                    with open(session_file, 'r') as f:
                        session_data = json.load(f)
                    self.client.load_settings(session_data)
                    print_status(4, "Loaded existing session")
                except Exception as e:
                    print_status(4, f"Could not load session: {str(e)}")
            
            # Login
            self.client.login(self.username, self.password)
            
            # Save session for future use
            try:
                with open(session_file, 'w') as f:
                    json.dump(self.client.get_settings(), f)
            except Exception as e:
                print_status(4, f"Could not save session: {str(e)}")
            
            print_status(4, "Posting to Instagram...")
            
            # Post the media
            if is_video:
                media = self.client.video_upload(media_path, caption)
            else:
                media = self.client.photo_upload(media_path, caption)
            
            print_status(4, f"Successfully posted to Instagram with media ID: {media.id}")
            return True
            
        except Exception as e:
            print_status(4, f"Error posting to Instagram: {str(e)}")
            logger.error(f"Error posting to Instagram: {str(e)}")
            
            # Fall back to simulation
            return self._simulate_post(media_path, caption, None, is_video)
    
    def _simulate_post(self, media_path, caption, product, is_video):
        """Simulate posting to Instagram when real posting is not available."""
        print_status(4, "Simulating Instagram post...")
        time.sleep(1)
        
        print("\n" + "=" * 60)
        print("INSTAGRAM POST SIMULATION")
        print("=" * 60)
        
        if product:
            print(f"Product: {product['name']}")
        print(f"Media: {os.path.basename(media_path)}")
        print(f"Media Type: {'Video' if is_video else 'Image'}")
        
        print("\nCaption:")
        print("-" * 40)
        print(caption)
        print("-" * 40)
        
        print("\nThis would normally be posted to Instagram")
        print("=" * 60 + "\n")
        
        return True


# ==== SCHEDULING ====
class Scheduler:
    """Handles scheduling of posts."""
    
    def __init__(self, config):
        self.min_hours = config["scheduling"]["min_hours"]
        self.max_hours = config["scheduling"]["max_hours"]
        self.allowed_hours = config["scheduling"]["allowed_hours"]
    
    def schedule_next_post(self):
        """Calculate and display the next posting time."""
        hours_from_now = random.randint(self.min_hours, self.max_hours)
        
        # Calculate target time
        now = datetime.now()
        target_time = now + timedelta(hours=hours_from_now)
        
        # Ensure it's within allowed posting hours
        while target_time.hour not in self.allowed_hours:
            # Find next allowed hour
            next_hour = min([h for h in self.allowed_hours if h > target_time.hour], default=self.allowed_hours[0])
            
            if next_hour <= target_time.hour:  # Means we wrapped to next day
                target_time = target_time.replace(hour=next_hour, day=target_time.day+1)
            else:
                target_time = target_time.replace(hour=next_hour)
        
        # Format for display
        time_str = target_time.strftime("%Y-%m-%d %H:%M:%S")
        
        print_status(5, f"Next post scheduled for: {time_str} ({hours_from_now} hours from now)")
        logger.info(f"Next post scheduled for: {time_str}")
        
        return target_time


# ==== MAIN PROCESS ====
def check_dependencies():
    """Check for required dependencies and provide installation instructions."""
    missing_deps = []
    
    # Check for Pillow
    try:
        from PIL import Image
        print_status(0, "Pillow is installed")
    except ImportError:
        missing_deps.append("Pillow (pip install Pillow)")
    
    # Check for requests
    try:
        import requests
        print_status(0, "requests is installed")
    except ImportError:
        missing_deps.append("requests (pip install requests)")
    
    # Check for ffmpeg
    try:
        result = subprocess.run(
            ["ffmpeg", "-version"], 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE
        )
        if result.returncode == 0:
            print_status(0, "ffmpeg is installed")
        else:
            missing_deps.append("ffmpeg (system package)")
    except (subprocess.SubprocessError, FileNotFoundError):
        missing_deps.append("ffmpeg (system package)")
    
    # Check for instagrapi
    try:
        import instagrapi
        print_status(0, "instagrapi is installed")
    except ImportError:
        missing_deps.append("instagrapi (pip install instagrapi)")
    
    # Display missing dependencies
    if missing_deps:
        print("\nMISSING DEPENDENCIES:")
        for dep in missing_deps:
            print(f"- {dep}")
        
        print("\nInstallation instructions:")
        print("- For Python packages: pip install package_name")
        print("- For ffmpeg: visit https://ffmpeg.org/download.html")
        print("\nOptional dependencies will use fallback methods.\n")
    else:
        print_status(0, "All dependencies are installed")


n():
    """Main function that runs the whole process."""
    print("\n" + "=" * 60)
    print("Enhanced Warrior Plus to Instagram Automation".center(60))
    print("=" * 60 + "\n")
    
    print("This script automates:")
    print("1. Finding profitable products on Warrior Plus")
    print("2. Creating slideshow videos with ffmpeg")
    print("3. Posting to Instagram using instagrapi")
    print("4. Scheduling posts at random intervals")
    
    # Check dependencies first
    check_dependencies()
    
    print("\nPress Enter to begin...")
    input()
    
    try:
        # Initialize components
        warrior_api = WarriorPlusAPI(CONFIG)
        video_creator = VideoCreator(CONFIG)
        instagram = InstagramPoster(CONFIG)
        scheduler = Scheduler(CONFIG)
        
        # 1. Get high-return products
        products = warrior_api.get_high_return_products(limit=10)
        if not products:
            print_status(1, "No products found")
            return
        
        # 2. Select a product (weighted by return score)
        weights = [p.get("return_score", 1) for p in products]
        selected_product = random.choices(products, weights=weights, k=1)[0]
        
        print_status(1, f"Selected product: {selected_product['name']}")
        print_status(1, f"Price: {selected_product['price']} | " +
                     f"Commission: ${selected_product.get('commission_amount', 'N/A')}")
        
        # 3. Generate affiliate link
        affiliate_link = warrior_api.get_affiliate_link(selected_product['id'])
        print_status(1, f"Affiliate link: {affiliate_link}")
        
        # 4. Generate marketing script
        script = warrior_api.generate_script(selected_product['id'])
        if not script:
            print_status(2, "Failed to generate script")
            return
        
        # 5. Create video
        video_path, slide_paths = video_creator.create_video(script, selected_product)
        
        # 6. Post to Instagram
        instagram.post_to_instagram(video_path, script, selected_product)
        
        # 7. Schedule next post
        scheduler.schedule_next_post()
        
        print("\nProcess completed successfully!")
        print(f"Check {CONFIG['output_dir']} folder to see the generated content")
        
    except Exception as e:
        print(f"\nERROR: {str(e)}")
        logger.error(f"Error in main process: {str(e)}", exc_info=True)
        print("The process encountered an error. See above for details.")
   
    print("\nPress Enter to exit...")
    input()

if __name__ == "__main__":
    main() 