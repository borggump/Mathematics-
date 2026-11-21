
import os
import random
import time
from datetime import datetime, timedelta
from PIL import Image, ImageDraw, ImageFont

# Create output directories
output_dir = "warrior_videos"
slides_dir = os.path.join(output_dir, "slides")
os.makedirs(output_dir, exist_ok=True)
os.makedirs(slides_dir, exist_ok=True)

# Mock product data
PRODUCTS = [
    {
        "name": "Ultimate Traffic Blueprint",
        "description": "Get unlimited traffic to your offers using this proven system.",
        "price": "$27.00",
        "benefits": [
            "Save time and increase your productivity",
            "Generate more income with less effort",
            "Access proven methods used by top earners"
        ]
    },
    {
        "name": "AI Content Creator Pro",
        "description": "Generate high-converting content in seconds with this AI tool.",
        "price": "$47.00",
        "benefits": [
            "Create content 10x faster than manual methods",
            "Boost your conversions with proven frameworks",
            "Never face writer's block again"
        ]
    }
]

def print_status(step, message):
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] STEP {step}: {message}")
    time.sleep(0.5)

def create_slide(text, number, total, filename):
    # Create a new image
    img = Image.new('RGB', (1080, 1080), color='navy')
    draw = ImageDraw.Draw(img)
    
    # Add text
    draw.text((50, 50), f"Slide {number}/{total}", fill="white")
    draw.text((50, 150), text, fill="white")
    
    # Save the image
    img.save(filename)
    print_status(3, f"Created slide {number}: {filename}")
    
    return filename

def create_slides_for_product(product):
    print_status(2, f"Creating slides for {product['name']}")
    
    slides = []
    
    # Title slide
    slides.append(create_slide(
        f"INTRODUCING: {product['name']}",
        1, 5, os.path.join(slides_dir, "slide_01.jpg")
    ))
    
    # Description slide
    slides.append(create_slide(
        product['description'],
        2, 5, os.path.join(slides_dir, "slide_02.jpg")
    ))
    
    # Benefits slides
    for i, benefit in enumerate(product['benefits']):
        slides.append(create_slide(
            f"BENEFIT #{i+1}: {benefit}",
            i+3, 5, os.path.join(slides_dir, "slide_0{i+3}.jpg")
        ))
    
    # Price slide
    slides.append(create_slide(
        f"SPECIAL OFFER: ONLY {product['price']}",
        5, 5, os.path.join(slides_dir, "slide_05.jpg")
    ))
    
    return slides

def simulate_instagram_post(product, slides):
    print_status(4, "Preparing Instagram post")
    
    # Create caption with hashtags
    hashtags = "#makemoney #affiliate #onlinebusiness #marketing"
    
    caption = f"""
NEW PRODUCT ALERT!

Just discovered {product['name']}! This is a game-changer.

{product['description']}

Available now for {product['price']}!

Click the link in my bio to learn more.

{hashtags}
    """
    
    print_status(4, "Simulating Instagram post...")
    print("\n=== INSTAGRAM POST SIMULATION ===")
    print(f"Product: {product['name']}")
    print(f"Number of slides: {len(slides)}")
    print("\nCaption:")
    print("-" * 40)
    print(caption)
    print("-" * 40)
    
    return True

def schedule_next_post():
    hours = random.randint(12, 48)
    next_time = datetime.now() + timedelta(hours=hours)
    time_str = next_time.strftime("%Y-%m-%d %H:%M:%S")
    
    print_status(5, f"Next post scheduled for: {time_str} ({hours} hours from now)")

def main():
    print("\n=== Warrior Plus to Instagram Automation ===\n")
    
    # Step 1: Select a product
    product = random.choice(PRODUCTS)
    print_status(1, f"Selected product: {product['name']}")
    print_status(1, f"Price: {product['price']}")
    
    # Step 2 & 3: Create slides
    slides = create_slides_for_product(product)
    print_status(3, f"Created {len(slides)} slides")
    
    # Step 4: Simulate Instagram post
    simulate_instagram_post(product, slides)
    
    # Step 5: Schedule next post
    schedule_next_post()
    
    print("\nProcess completed successfully!")
    print(f"Check {slides_dir} folder to see the generated slides")

if __name__ == "__main__":
    main()
