#!/usr/bin/env python3
"""
Simple Working Version - Warrior Plus to Instagram Automation
Fixed to work on all systems by removing emoji support
"""

import os
import time
import random
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
import textwrap

# Create output directory
output_dir = "warrior_videos"
os.makedirs(output_dir, exist_ok=True)

# Mock product data (no API needed)
MOCK_PRODUCTS = [
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

def print_status(step, message):
    """Print a status update with timestamp."""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] STEP {step}: {message}")
    # Add a small delay to make progress visible
    time.sleep(0.5)

def select_product():
    """Select a product from mock data."""
    print_status(1, "Finding high-return products...")
    time.sleep(1)
    
    # Randomly select a product from our mock data
    product = random.choice(MOCK_PRODUCTS)
    
    print_status(1, f"Selected product: {product['name']}")
    print_status(1, f"Price: {product['price']} | Commission: ${product['commission_amount']}")
    
    # Generate an affiliate link
    affiliate_link = f"https://warriorplus.com/o2/a/youraffid/{product['id']}"
    print_status(1, f"Generated affiliate link: {affiliate_link}")
    
    return product

def generate_script(product):
    """Generate a video script for the product."""
    print_status(2, "Generating marketing script...")
    time.sleep(1)
    
    # Extract key details
    name = product["name"]
    description = product["description"]
    price = product["price"]
    
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
    print_status(2, f"Script preview: {script[:100]}...")
    
    return script

def create_slide_image(title, subtitle, slide_number, total_slides):
    """Create a simple slide image with text."""
    print_status(3, f"Creating slide {slide_number}/{total_slides}: {title}")
    
    # Create a new image
    width, height = 1080, 1920  # Instagram portrait size
    image = Image.new("RGB", (width, height), color="#000080")  # Navy blue background
    draw = ImageDraw.Draw(image)
    
    # Add slide number
    draw.text((width-80, 40), f"{slide_number}/{total_slides}", fill="white")
    
    # Try to use a nice font, fall back to default if not available
    try:
        # Try common fonts that might be available
        font_size = 60
        small_font_size = 40
        
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
            # If no font found, use default
            title_font = ImageFont.load_default()
            subtitle_font = ImageFont.load_default()
            
    except Exception:
        # Fall back to default font if anything goes wrong
        title_font = ImageFont.load_default()
        subtitle_font = ImageFont.load_default()
    
    # Wrap text to fit on image
    wrapped_title = textwrap.fill(title, width=25)
    
    # Calculate text position - centered horizontally, near top vertically
    try:
        # Calculate title position - modern way
        title_bbox = draw.textbbox((0, 0), wrapped_title, font=title_font)
        title_width = title_bbox[2] - title_bbox[0]
        title_height = title_bbox[3] - title_bbox[1]
        title_position = ((width - title_width) // 2, height // 4 - title_height // 2)
    except AttributeError:
        # Fallback for older PIL versions
        title_width, title_height = draw.textsize(wrapped_title, font=title_font)
        title_position = ((width - title_width) // 2, height // 4 - title_height // 2)
    
    # Draw title
    draw.text(title_position, wrapped_title, fill="white", font=title_font)
    
    # Draw subtitle
    wrapped_subtitle = textwrap.fill(subtitle, width=35)
    
    try:
        # Calculate subtitle position - modern way
        subtitle_bbox = draw.textbbox((0, 0), wrapped_subtitle, font=subtitle_font)
        subtitle_width = subtitle_bbox[2] - subtitle_bbox[0]
        subtitle_height = subtitle_bbox[3] - subtitle_bbox[1]
        subtitle_position = ((width - subtitle_width) // 2, height // 2 - subtitle_height // 2)
    except AttributeError:
        # Fallback for older PIL versions
        subtitle_width, subtitle_height = draw.textsize(wrapped_subtitle, font=subtitle_font)
        subtitle_position = ((width - subtitle_width) // 2, height // 2 - subtitle_height // 2)
    
    draw.text(subtitle_position, wrapped_subtitle, fill="white", font=subtitle_font)
    
    # Add decorative elements instead of emojis
    # Draw stars in corners instead of emojis
    draw.text((50, 50), "*", fill="white", font=title_font)
    draw.text((width-100, height-100), "*", fill="white", font=title_font)
    
    return image

def create_simple_video(product, script):
    """Create a simple slideshow 'video' using a series of images."""
    print_status(3, f"Creating video for: {product['name']}")
    
    # Parse script into slides
    paragraphs = [p.strip() for p in script.split('\n\n') if p.strip()]
    
    # Create a series of slide images
    slide_images = []
    slides_dir = os.path.join(output_dir, "slides")
    os.makedirs(slides_dir, exist_ok=True)
    
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
        slide_img = create_slide_image(title, subtitle, i+1, total_slides)
        
        # Save slide
        slide_path = os.path.join(slides_dir, f"slide_{i+1:02d}.jpg")
        slide_img.save(slide_path, "JPEG", quality=95)
        slide_images.append(slide_path)
        
        # Wait a bit to show progress
        time.sleep(0.5)
    
    # Create a combined "video" (just all slides in sequence for this demo)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    video_name = f"{product['name'].replace(' ', '_')}_{timestamp}"
    
    # Since we can't easily create actual videos without dependencies,
    # we'll just save the slides and consider it our "video"
    print_status(3, f"Created {len(slide_images)} slides for video: {video_name}")
    print_status(3, f"Slides saved in: {slides_dir}")
    
    # Create a mock video path
    video_path = os.path.join(output_dir, f"{video_name}.txt")
    
    # Save information about the "video" to a text file
    with open(video_path, 'w') as f:
        f.write(f"Video: {product['name']}\n")
        f.write(f"Created: {timestamp}\n")
        f.write(f"Number of slides: {len(slide_images)}\n\n")
        f.write("SCRIPT:\n\n")
        f.write(script)
    
    print_status(3, f"Video information saved to: {video_path}")
    return video_path, slide_images

def simulate_instagram_post(video_path, product):
    """Simulate posting to Instagram."""
    print_status(4, "Preparing Instagram post...")
    time.sleep(1)
    
    # Create Instagram caption
    hashtags = " ".join([
        "#makemoney", "#onlinebusiness", "#affiliate", "#warriorplus",
        "#digitalmarketing", "#passiveincome", "#sidehustle"
    ])
    
    caption = f"""
    NEW PRODUCT ALERT!
    
    Just discovered {product['name']}! This is a game-changer for anyone looking to improve their results.
    
    {product['description']}
    
    Limited time offer available now at {product['price']}!
    
    Click the link in my bio to learn more!
    
    {hashtags}
    """
    
    print_status(4, "Prepared Instagram caption")
    print_status(4, f"Caption preview: {caption[:100]}...")
    
    print_status(4, "Simulating Instagram post...")
    time.sleep(2)
    
    print("\n" + "=" * 50)
    print("INSTAGRAM POST SIMULATION")
    print("=" * 50)
    print(f"Video: {os.path.basename(video_path)}")
    print(f"Product: {product['name']}")
    print("\nCaption:")
    print("-" * 40)
    print(caption)
    print("-" * 40)
    print("\nThis would normally be posted to Instagram")
    print("=" * 50 + "\n")
    
    return True

def schedule_next_post():
    """Simulate scheduling the next post."""
    min_hours = 12
    max_hours = 72
    hours = random.randint(min_hours, max_hours)
    
    now = datetime.now()
    next_time = now.replace(hour=(now.hour + hours) % 24)
    time_str = next_time.strftime("%Y-%m-%d %H:%M:%S")
    
    print_status(5, f"Scheduling next post for: {time_str} ({hours} hours from now)")
    
    return True

def main():
    """Main function that runs the whole process."""
    print("\n" + "=" * 60)
    print("Simple Working Version - Warrior Plus to Instagram Automation".center(60))
    print("=" * 60 + "\n")
    
    print("This script demonstrates the process of:")
    print("1. Finding profitable products on Warrior Plus")
    print("2. Creating slideshow videos from text")
    print("3. Posting to Instagram on a randomized schedule")
    print("\nPress Enter to begin...")
    input()
    
    # Start the process
    try:
        # 1. Select a product
        product = select_product()
        
        # 2. Generate script
        script = generate_script(product)
        
        # 3. Create video
        video_path, slide_images = create_simple_video(product, script)
        
        # 4. Simulate Instagram post
        simulate_instagram_post(video_path, product)
        
        # 5. Schedule next post
        schedule_next_post()
        
        print("\nProcess completed successfully!")
        print(f"Check {output_dir} folder to see the generated content")
        
    except Exception as e:
        print(f"\nERROR: {str(e)}")
        print("The process encountered an error. See above for details.")
    
    print("\nPress Enter to exit...")
    input()

if __name__ == "__main__":
    main()