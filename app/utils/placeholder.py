import os
import io
import random
from PIL import Image, ImageDraw, ImageFont, ImageColor
import logging

logger = logging.getLogger(__name__)

# Default dimensions for placeholder images
DEFAULT_WIDTH = 800
DEFAULT_HEIGHT = 600
DEFAULT_AVATAR_SIZE = 200
DEFAULT_ACHIEVEMENT_SIZE = 128
DEFAULT_EVENT_LOGO_SIZE = 400
DEFAULT_NEWS_SIZE = 800

# Updated thematic color palettes with more sophisticated colors
COLOR_PALETTES = {
    'default': ['#3498db', '#2980b9', '#2c3e50', '#1abc9c', '#16a085'],
    'profile': ['#6c5ce7', '#a29bfe', '#74b9ff', '#0984e3', '#dfe6e9'],  # Purple/blue tones
    'event': ['#9b59b6', '#8e44ad', '#2980b9', '#3498db', '#1abc9c'],
    'news': ['#2d3436', '#636e72', '#b2bec3', '#dfe6e9', '#0984e3'],  # Refined grayscale with blue accent
    'achievement': ['#2ecc71', '#27ae60', '#1abc9c', '#16a085', '#3498db']
}

# More unique and diverse symbols for different contexts
SYMBOLS = {
    'profile': ['🎭', '🧠', '🚀', '🌟', '🔍', '🌈'],  # More diverse and interesting symbols
    'event': ['🎪', '🎭', '📅', '📆', '🎤', '📢', '🎬', '🎮', '🏆'],
    'news': ['📰', '🌐', '📊', '💡', '🔖', '📋'],  # More professional news symbols
    'achievement': ['🏆', '🥇', '🥈', '🥉', '⭐', '🌟', '🎖️', '🏅']
}

# More sophisticated patterns
PATTERNS = ['gradient', 'wave', 'geometric', 'modern_dots', 'minimal']

def draw_gradient(draw, width, height, color1, color2, direction='horizontal'):
    """Draw a gradient background from color1 to color2"""
    if direction == 'horizontal':
        for x in range(width):
            # Calculate gradient
            r = int(color1[0] + (color2[0] - color1[0]) * x / width)
            g = int(color1[1] + (color2[1] - color1[1]) * x / width)
            b = int(color1[2] + (color2[2] - color1[2]) * x / width)
            # Draw line
            draw.line([(x, 0), (x, height)], fill=(r, g, b))
    else:  # vertical
        for y in range(height):
            # Calculate gradient
            r = int(color1[0] + (color2[0] - color1[0]) * y / height)
            g = int(color1[1] + (color2[1] - color1[1]) * y / height)
            b = int(color1[2] + (color2[2] - color1[2]) * y / height)
            # Draw line
            draw.line([(0, y), (width, y)], fill=(r, g, b))

def draw_wave(draw, width, height, color1, color2):
    """Draw a wave pattern background"""
    # Fill background
    draw.rectangle([(0, 0), (width, height)], fill=color1)
    
    # Draw wave pattern
    amplitude = height / 10
    frequency = 0.02
    phase = random.uniform(0, 3.14)
    
    import math
    
    # Draw several waves with different parameters
    for wave_num in range(3):
        points = []
        y_offset = height * (wave_num + 1) / 4
        for x in range(0, width + 1, 5):
            y = y_offset + amplitude * math.sin(frequency * x + phase + wave_num)
            points.append((x, y))
        
        # Add bottom points to create a filled shape
        points.append((width, height))
        points.append((0, height))
        
        # Draw the wave
        wave_color = (
            int(color2[0] * (0.5 + 0.5 * (wave_num / 2))),
            int(color2[1] * (0.5 + 0.5 * (wave_num / 2))),
            int(color2[2] * (0.5 + 0.5 * (wave_num / 2)))
        )
        draw.polygon(points, fill=wave_color)

def draw_geometric(draw, width, height, color1, color2):
    """Draw a geometric pattern with triangles and shapes"""
    # Fill background
    draw.rectangle([(0, 0), (width, height)], fill=color1)
    
    # Draw geometric shapes
    num_shapes = random.randint(3, 7)
    for _ in range(num_shapes):
        shape_type = random.choice(['triangle', 'rectangle', 'circle'])
        
        # Random position and size
        x = random.randint(0, width)
        y = random.randint(0, height)
        size = random.randint(min(width, height) // 8, min(width, height) // 4)
        
        # Random shape color (semi-transparent blend of color2)
        alpha = random.randint(30, 80)
        shape_color = (color2[0], color2[1], color2[2], alpha)
        
        # Draw shape
        if shape_type == 'triangle':
            points = [
                (x, y),
                (x + size, y + size // 2),
                (x, y + size)
            ]
            draw.polygon(points, fill=shape_color)
        elif shape_type == 'rectangle':
            draw.rectangle([(x, y), (x + size, y + size)], fill=shape_color)
        else:  # circle
            draw.ellipse([(x, y), (x + size, y + size)], fill=shape_color)

def draw_modern_dots(draw, width, height, color1, color2):
    """Draw a modern dot pattern with varied sizes"""
    # Fill background
    draw.rectangle([(0, 0), (width, height)], fill=color1)
    
    # Draw dots of various sizes
    num_dots = random.randint(10, 30)
    for _ in range(num_dots):
        x = random.randint(0, width)
        y = random.randint(0, height)
        size = random.randint(width // 40, width // 15)
        
        # Vary the color slightly
        r_offset = random.randint(-20, 20)
        g_offset = random.randint(-20, 20)
        b_offset = random.randint(-20, 20)
        
        dot_color = (
            max(0, min(255, color2[0] + r_offset)),
            max(0, min(255, color2[1] + g_offset)),
            max(0, min(255, color2[2] + b_offset))
        )
        
        draw.ellipse([(x, y), (x + size, y + size)], fill=dot_color)

def draw_minimal(draw, width, height, color1, color2):
    """Draw a minimal design with simple lines or shapes"""
    # Fill background
    draw.rectangle([(0, 0), (width, height)], fill=color1)
    
    # Draw a simple accent shape
    shape_type = random.choice(['line', 'corner', 'side'])
    
    if shape_type == 'line':
        line_thickness = max(2, min(width, height) // 50)
        if random.choice([True, False]):  # horizontal
            y_pos = random.randint(height // 3, 2 * height // 3)
            draw.rectangle([(0, y_pos), (width, y_pos + line_thickness)], fill=color2)
        else:  # vertical
            x_pos = random.randint(width // 3, 2 * width // 3)
            draw.rectangle([(x_pos, 0), (x_pos + line_thickness, height)], fill=color2)
    
    elif shape_type == 'corner':
        line_thickness = max(3, min(width, height) // 40)
        corner = random.choice(['tl', 'tr', 'bl', 'br'])
        
        if corner == 'tl':  # top-left
            draw.rectangle([(0, 0), (width // 3, line_thickness)], fill=color2)
            draw.rectangle([(0, 0), (line_thickness, height // 3)], fill=color2)
        elif corner == 'tr':  # top-right
            draw.rectangle([(2 * width // 3, 0), (width, line_thickness)], fill=color2)
            draw.rectangle([(width - line_thickness, 0), (width, height // 3)], fill=color2)
        elif corner == 'bl':  # bottom-left
            draw.rectangle([(0, height - line_thickness), (width // 3, height)], fill=color2)
            draw.rectangle([(0, 2 * height // 3), (line_thickness, height)], fill=color2)
        else:  # bottom-right
            draw.rectangle([(2 * width // 3, height - line_thickness), (width, height)], fill=color2)
            draw.rectangle([(width - line_thickness, 2 * height // 3), (width, height)], fill=color2)
    
    else:  # side
        side = random.choice(['top', 'right', 'bottom', 'left'])
        side_width = min(width, height) // 6
        
        if side == 'top':
            draw.rectangle([(0, 0), (width, side_width)], fill=color2)
        elif side == 'right':
            draw.rectangle([(width - side_width, 0), (width, height)], fill=color2)
        elif side == 'bottom':
            draw.rectangle([(0, height - side_width), (width, height)], fill=color2)
        else:  # left
            draw.rectangle([(0, 0), (side_width, height)], fill=color2)

def get_placeholder_image(type='default', width=None, height=None, text=None):
    """Generate a thematic placeholder image based on context type
    
    Args:
        type (str): Type of placeholder ('profile', 'event', 'news', 'achievement')
        width (int): Width of the image
        height (int): Height of the image
        text (str): Optional text to display on the image
    
    Returns:
        BytesIO: Image data as a BytesIO object
    """
    # Set dimensions based on type
    if width is None or height is None:
        if type == 'profile':
            width = height = DEFAULT_AVATAR_SIZE
        elif type == 'achievement':
            width = height = DEFAULT_ACHIEVEMENT_SIZE
        elif type == 'event':
            width = height = DEFAULT_EVENT_LOGO_SIZE
        elif type == 'news':
            width = DEFAULT_NEWS_SIZE
            height = DEFAULT_HEIGHT
        else:
            width = DEFAULT_WIDTH
            height = DEFAULT_HEIGHT
    
    # Create new image with white background
    image = Image.new('RGB', (width, height), (255, 255, 255))
    draw = ImageDraw.Draw(image)
    
    # Get color palette for the type
    palette = COLOR_PALETTES.get(type, COLOR_PALETTES['default'])
    
    # Get random colors from palette
    main_color = random.choice(palette)
    secondary_color = random.choice([c for c in palette if c != main_color])
    
    # Convert hex to RGB
    main_rgb = ImageColor.getrgb(main_color)
    secondary_rgb = ImageColor.getrgb(secondary_color)
    
    # Choose a pattern appropriate for the type
    if type == 'news':
        pattern = random.choice(['minimal', 'gradient', 'geometric'])
    elif type == 'profile':
        pattern = random.choice(['gradient', 'modern_dots', 'minimal'])
    else:
        pattern = random.choice(PATTERNS)
    
    # Draw background pattern
    if pattern == 'gradient':
        draw_gradient(draw, width, height, main_rgb, secondary_rgb, 
                      direction=random.choice(['horizontal', 'vertical']))
    elif pattern == 'wave':
        draw_wave(draw, width, height, main_rgb, secondary_rgb)
    elif pattern == 'geometric':
        draw_geometric(draw, width, height, main_rgb, secondary_rgb)
    elif pattern == 'modern_dots':
        draw_modern_dots(draw, width, height, main_rgb, secondary_rgb)
    elif pattern == 'minimal':
        draw_minimal(draw, width, height, main_rgb, secondary_rgb)
    else:
        # Fallback to gradient
        draw_gradient(draw, width, height, main_rgb, secondary_rgb, 'horizontal')
    
    # Choose a random symbol for the type
    symbols = SYMBOLS.get(type, ['📷'])
    symbol = random.choice(symbols)
    
    # Calculate font size (proportional to image dimensions)
    symbol_font_size = min(width, height) // 3
    text_font_size = min(width, height) // 10
    
    try:
        # Try to get a font, or use default
        symbol_font = ImageFont.truetype("arial.ttf", symbol_font_size)
        text_font = ImageFont.truetype("arial.ttf", text_font_size)
    except IOError:
        # Use default font if custom font fails
        symbol_font = ImageFont.load_default()
        text_font = ImageFont.load_default()
    
    # Calculate position for the symbol (center)
    symbol_width, symbol_height = draw.textbbox((0, 0), symbol, font=symbol_font)[2:]
    symbol_position = ((width - symbol_width) // 2, (height - symbol_height) // 3)
    
    # Draw the symbol
    draw.text(symbol_position, symbol, font=symbol_font, fill=secondary_rgb)
    
    # Add text if provided, otherwise use type as text
    display_text = text if text else f"Default {type.capitalize()}"
    
    # Calculate text position (centered at bottom)
    text_width, text_height = draw.textbbox((0, 0), display_text, font=text_font)[2:]
    text_position = ((width - text_width) // 2, height - text_height - height // 10)
    
    # Draw text with a slight shadow for readability
    draw.text((text_position[0]+2, text_position[1]+2), display_text, 
              font=text_font, fill=(0, 0, 0, 128))
    draw.text(text_position, display_text, font=text_font, fill=(255, 255, 255))
    
    # Save image to BytesIO
    img_io = io.BytesIO()
    image.save(img_io, 'PNG')
    img_io.seek(0)
    
    return img_io

def generate_default_placeholders(app_static_folder):
    """Generate default placeholder images for the application
    
    Args:
        app_static_folder (str): Path to the static folder
    """
    image_folder = os.path.join(app_static_folder, 'img')
    
    # Define placeholder types and their paths
    placeholders = {
        'profile': {
            'path': os.path.join(image_folder, 'profile_pics', 'default.jpg'),
            'width': DEFAULT_AVATAR_SIZE,
            'height': DEFAULT_AVATAR_SIZE,
            'text': 'User Profile'
        },
        'event': {
            'path': os.path.join(image_folder, 'event_logos', 'default_event.jpg'),
            'width': DEFAULT_EVENT_LOGO_SIZE,
            'height': DEFAULT_EVENT_LOGO_SIZE,
            'text': 'Event'
        },
        'news': {
            'path': os.path.join(image_folder, 'news_images', 'default_news.jpg'),
            'width': DEFAULT_NEWS_SIZE,
            'height': DEFAULT_HEIGHT,
            'text': 'News'
        },
        'achievement': {
            'path': os.path.join(image_folder, 'achievement_icons', 'default_achievement.png'),
            'width': DEFAULT_ACHIEVEMENT_SIZE,
            'height': DEFAULT_ACHIEVEMENT_SIZE,
            'text': 'Achievement'
        },
        # Additional achievement types
        'achievement_participation': {
            'path': os.path.join(image_folder, 'achievement_icons', 'achievement_participation.png'),
            'width': DEFAULT_ACHIEVEMENT_SIZE,
            'height': DEFAULT_ACHIEVEMENT_SIZE,
            'text': 'Participation',
            'type': 'achievement'
        },
        'achievement_organizer': {
            'path': os.path.join(image_folder, 'achievement_icons', 'achievement_organizer.png'),
            'width': DEFAULT_ACHIEVEMENT_SIZE,
            'height': DEFAULT_ACHIEVEMENT_SIZE,
            'text': 'Organizer',
            'type': 'achievement'
        },
        'achievement_special': {
            'path': os.path.join(image_folder, 'achievement_icons', 'achievement_special.png'),
            'width': DEFAULT_ACHIEVEMENT_SIZE,
            'height': DEFAULT_ACHIEVEMENT_SIZE,
            'text': 'Special',
            'type': 'achievement'
        }
    }
    
    # Create the folders if they don't exist
    for placeholder_type, info in placeholders.items():
        folder = os.path.dirname(info['path'])
        if not os.path.exists(folder):
            try:
                os.makedirs(folder)
                logger.info(f"Created directory: {folder}")
            except Exception as e:
                logger.error(f"Error creating directory {folder}: {str(e)}")
                continue
        
        # Generate the placeholder image
        try:
            img_type = info.get('type', placeholder_type)
            img_io = get_placeholder_image(
                type=img_type,
                width=info['width'],
                height=info['height'],
                text=info['text']
            )
            
            # Save the image
            with open(info['path'], 'wb') as f:
                f.write(img_io.getvalue())
            
            logger.info(f"Generated placeholder image: {info['path']}")
        except Exception as e:
            logger.error(f"Error generating placeholder {info['path']}: {str(e)}")

if __name__ == "__main__":
    # Test the placeholder generator
    for img_type in ['profile', 'event', 'news', 'achievement']:
        img_io = get_placeholder_image(type=img_type)
        with open(f"test_{img_type}.png", 'wb') as f:
            f.write(img_io.getvalue()) 