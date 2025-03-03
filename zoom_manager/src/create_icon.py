#!/usr/bin/env python3
"""
Script to create macOS .icns icon file from a PNG image.
"""

import os
import subprocess
from PIL import Image

def create_icns():
    # Create iconset directory
    iconset_dir = "config/icon.iconset"
    os.makedirs(iconset_dir, exist_ok=True)
    
    # Create a simple icon image (you can replace this with your own icon)
    icon = Image.new('RGBA', (1024, 1024), (0, 0, 0, 0))
    icon.save(f"{iconset_dir}/icon_512x512@2x.png")
    
    # Generate other required sizes
    sizes = [16, 32, 64, 128, 256, 512, 1024]
    for size in sizes:
        if size <= 512:
            icon = Image.new('RGBA', (size, size), (0, 0, 0, 0))
            icon.save(f"{iconset_dir}/icon_{size}x{size}.png")
            if size <= 256:
                icon.save(f"{iconset_dir}/icon_{size//2}x{size//2}@2x.png")
    
    # Convert iconset to icns
    subprocess.run(['iconutil', '-c', 'icns', iconset_dir, '-o', 'config/icon.icns'])

if __name__ == "__main__":
    create_icns() 