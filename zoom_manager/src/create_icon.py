"""
Script to create the application icon
Generates a simple icon with a cloud and arrow design
"""

from PIL import Image, ImageDraw
import os

def create_icon():
    # Create a 1024x1024 image with transparency
    size = 1024
    image = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    
    # Draw cloud
    cloud_color = (52, 152, 219)  # Blue
    cloud_points = [
        (size * 0.2, size * 0.5),  # Left
        (size * 0.3, size * 0.3),  # Top left
        (size * 0.5, size * 0.2),  # Top
        (size * 0.7, size * 0.3),  # Top right
        (size * 0.8, size * 0.5),  # Right
        (size * 0.7, size * 0.7),  # Bottom right
        (size * 0.5, size * 0.8),  # Bottom
        (size * 0.3, size * 0.7),  # Bottom left
    ]
    draw.polygon(cloud_points, fill=cloud_color)
    
    # Draw arrow
    arrow_color = (46, 204, 113)  # Green
    arrow_points = [
        (size * 0.6, size * 0.4),  # Arrow head
        (size * 0.8, size * 0.5),  # Arrow tip
        (size * 0.6, size * 0.6),  # Arrow head
        (size * 0.6, size * 0.7),  # Arrow shaft
        (size * 0.4, size * 0.5),  # Arrow base
        (size * 0.6, size * 0.3),  # Arrow shaft
    ]
    draw.polygon(arrow_points, fill=arrow_color)
    
    # Save as PNG
    icon_dir = os.path.join(os.path.dirname(__file__), '..', 'config')
    os.makedirs(icon_dir, exist_ok=True)
    image.save(os.path.join(icon_dir, 'icon.png'))
    
    # Convert to ICNS (macOS icon format)
    os.system(f'iconutil -c icns {icon_dir}/icon.icns')

if __name__ == '__main__':
    create_icon() 