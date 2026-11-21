import math
from PIL import Image, ImageDraw

def create_dragon_fractal(order, size=800):
    """Create a dragon fractal using PIL instead of turtle"""
    # Create a new image with white background
    image = Image.new('RGB', (size, size), 'white')
    draw = ImageDraw.Draw(image)
    
    # Calculate dragon curve points
    def dragon_points(n):
        points = [(0, 0), (1, 0)]
        for i in range(n):
            px, py = points[-1]
            new_points = []
            for x, y in reversed(points[:-1]):
                # Rotate point 90 degrees clockwise around the end point
                nx = px + (y - py)
                ny = py - (x - px)
                new_points.append((nx, ny))
            points.extend(new_points)
        return points
    
    # Generate points
    points = dragon_points(order)
    
    # Find bounds to scale the image
    xs = [x for x, y in points]
    ys = [y for x, y in points]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    
    # Scale factor to fit in the image
    scale = min(
        (size - 40) / (max_x - min_x),
        (size - 40) / (max_y - min_y)
    )
    
    # Center offset
    offset_x = (size - (max_x - min_x) * scale) / 2 - min_x * scale
    offset_y = (size - (max_y - min_y) * scale) / 2 - min_y * scale
    
    # Scale and convert points
    scaled_points = [
        (x * scale + offset_x, y * scale + offset_y)
        for x, y in points
    ]
    
    # Draw lines
    for i in range(len(scaled_points) - 1):
        draw.line(
            [scaled_points[i], scaled_points[i + 1]],
            fill='black',
            width=2
        )
    
    return image

def main():
    print("Creating Dragon Fractal...")
    print("This may take a moment...")
    
    try:
        # Create the fractal
        order = 12  # Adjust this for different levels of detail
        image = create_dragon_fractal(order)
        
        # Save the image
        output_file = "/storage/emulated/0/Download/dragon_fractal.png"
        image.save(output_file)
        
        print(f"\nFractal created successfully!")
        print(f"Image saved to: {output_file}")
        
    except Exception as e:
        print(f"Error creating fractal: {str(e)}")

if __name__ == "__main__":
    main()
    input("\nPress Enter to continue...")