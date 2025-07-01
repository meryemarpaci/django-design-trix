#!/usr/bin/env python
"""
Create placeholder images for triX project
This script creates beautiful gradient placeholder images for the project.
Run this script to generate images in the static/images directory.
"""

import os
from PIL import Image, ImageDraw, ImageFilter, ImageFont
import numpy as np
import random
import argparse

def create_gradient_image(width, height, colors, filename, add_noise=True, blur=True):
    """Create a beautiful gradient image with optional noise."""
    # Create base image with gradient
    img = Image.new('RGBA', (width, height), color=0)
    draw = ImageDraw.Draw(img)
    
    # Draw gradient - vertical, horizontal or radial
    gradient_type = random.choice(['vertical', 'horizontal', 'radial'])
    
    if gradient_type == 'vertical':
        for y in range(height):
            # Calculate gradient position
            r = y / height
            # Interpolate between colors
            r, g, b = [int(colors[0][i] * (1 - r) + colors[1][i] * r) for i in range(3)]
            draw.line([(0, y), (width, y)], fill=(r, g, b))
    
    elif gradient_type == 'horizontal':
        for x in range(width):
            # Calculate gradient position
            r = x / width
            # Interpolate between colors
            r, g, b = [int(colors[0][i] * (1 - r) + colors[1][i] * r) for i in range(3)]
            draw.line([(x, 0), (x, height)], fill=(r, g, b))
    
    else:  # radial
        for y in range(height):
            for x in range(width):
                # Calculate distance from center (normalized)
                center_x, center_y = width / 2, height / 2
                distance = np.sqrt((x - center_x) ** 2 + (y - center_y) ** 2)
                max_distance = np.sqrt(center_x ** 2 + center_y ** 2)
                r = min(distance / max_distance, 1.0)
                
                # Interpolate between colors
                r_val, g_val, b_val = [int(colors[0][i] * (1 - r) + colors[1][i] * r) for i in range(3)]
                img.putpixel((x, y), (r_val, g_val, b_val))
    
    # Add noise if requested
    if add_noise:
        noise = np.random.randint(0, 30, (height, width, 3), dtype=np.uint8)
        noise_img = Image.fromarray(noise, 'RGB')
        img = Image.blend(img, noise_img.convert('RGBA'), 0.1)
    
    # Add blur if requested
    if blur:
        img = img.filter(ImageFilter.GaussianBlur(radius=3))
    
    # Add some geometric elements for style
    add_geometric_elements(draw, width, height)
    
    # Convert to RGB if saving as JPEG
    if filename.lower().endswith(('.jpg', '.jpeg')):
        # Create a white background
        background = Image.new('RGB', img.size, (255, 255, 255))
        # Paste the image with alpha channel onto the background
        background.paste(img, mask=img.split()[3])  # Use alpha channel as mask
        img = background
    
    # Save the image
    img.save(filename)
    print(f"Created {filename}")
    return img

def add_geometric_elements(draw, width, height):
    """Add some geometric elements to make the image more interesting."""
    num_elements = random.randint(3, 8)
    
    for _ in range(num_elements):
        # Choose shape type
        shape_type = random.choice(['circle', 'rectangle', 'line'])
        
        # Random size - smaller elements
        size = min(width, height) * random.uniform(0.05, 0.2)
        
        # Random position
        x = random.randint(0, width)
        y = random.randint(0, height)
        
        # Random color - semi-transparent white or purple
        color = (
            random.randint(150, 255),
            random.randint(150, 255),
            random.randint(200, 255),
            random.randint(30, 100)
        )
        
        # Draw the shape
        if shape_type == 'circle':
            draw.ellipse((x, y, x + size, y + size), fill=color)
        elif shape_type == 'rectangle':
            draw.rectangle((x, y, x + size, y + size), fill=color)
        else:  # line
            line_width = int(size * 0.1) + 1
            end_x = x + random.randint(-int(size), int(size))
            end_y = y + random.randint(-int(size), int(size))
            draw.line((x, y, end_x, end_y), fill=color, width=line_width)

def add_text_to_image(img, text, position=None):
    """Add text to an image."""
    draw = ImageDraw.Draw(img)
    width, height = img.size
    
    # Try to use a nice font if available, otherwise use default
    try:
        # Try multiple fonts that might be available on the system
        font_options = ["arial.ttf", "Arial.ttf", "DejaVuSans.ttf", "Verdana.ttf", "Tahoma.ttf"]
        font = None
        
        for font_name in font_options:
            try:
                font = ImageFont.truetype(font_name, size=int(height * 0.08))
                break
            except IOError:
                continue
        
        if font is None:
            font = ImageFont.load_default()
    except Exception:
        font = ImageFont.load_default()
    
    # Calculate text size
    try:
        # For newer Pillow versions
        text_bbox = draw.textbbox((0, 0), text, font=font)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]
    except AttributeError:
        # For older Pillow versions
        try:
            text_width, text_height = draw.textsize(text, font=font)
        except:
            # Fallback
            text_width, text_height = width // 4, height // 10
    
    # Position text in center if not specified
    if position is None:
        position = ((width - text_width) // 2, (height - text_height) // 2)
    
    # Add a shadow
    shadow_color = (0, 0, 0, 128)
    shadow_position = (position[0] + 2, position[1] + 2)
    
    try:
        draw.text(shadow_position, text, font=font, fill=shadow_color)
        draw.text(position, text, font=font, fill=(255, 255, 255, 230))
    except:
        # Fallback for older Pillow versions
        draw.text(shadow_position, text, fill=shadow_color)
        draw.text(position, text, fill=(255, 255, 255, 230))
    
    return img

def create_project_images():
    """Create a set of images for the triX project."""
    # Make sure the directory exists
    os.makedirs("static/images", exist_ok=True)
    
    # Purple-themed colors
    purples = [
        [(168, 85, 247), (236, 72, 153)],  # Purple to Pink
        [(91, 33, 182), (168, 85, 247)],   # Dark Purple to Purple
        [(67, 56, 202), (138, 43, 226)],   # Indigo to Purple
        [(124, 58, 237), (225, 29, 72)],   # Purple to Red
        [(104, 40, 128), (45, 212, 191)],  # Purple to Teal
    ]
    
    # Create project images
    for i in range(1, 7):
        colors = random.choice(purples)
        img = create_gradient_image(
            800, 600, 
            colors, 
            f"static/images/project{i}.jpg"
        )
        add_text_to_image(img, f"Project {i}")
    
    # Create a test image
    create_gradient_image(
        400, 300,
        [(168, 85, 247), (236, 72, 153)],
        "static/images/test-image.jpg"
    )

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create placeholder images for triX project")
    parser.add_argument("--force", action="store_true", help="Force recreation of images even if they exist")
    args = parser.parse_args()
    
    # Check if images already exist
    if not args.force and os.path.exists("static/images/project1.jpg"):
        print("Images already exist. Use --force to recreate them.")
    else:
        create_project_images() 