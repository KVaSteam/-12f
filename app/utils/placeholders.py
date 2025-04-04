import os
import random
from PIL import Image, ImageDraw, ImageFont, ImageColor
from io import BytesIO
import base64
import secrets
from flask import url_for, current_app
import math

def get_random_color(pastel=False):
    """
    Generate a random color, optionally as a pastel shade.
    
    Args:
        pastel (bool): Whether to generate a pastel color
        
    Returns:
        str: Hex color code
    """
    if pastel:
        # Generate pastel colors (higher brightness)
        r = random.randint(180, 255)
        g = random.randint(180, 255)
        b = random.randint(180, 255)
        return f"#{r:02x}{g:02x}{b:02x}"
    else:
        # Generate vibrant colors
        return "#{:06x}".format(random.randint(0, 0xFFFFFF))

def generate_profile_placeholder(output_path, username=None, size=200):
    """
    Generates a placeholder profile image based on the user's initials.
    
    Args:
        output_path (str): Path to save the image
        username (str): Username to generate initials from
        size (int): Size of the image in pixels
    """
    # Set up image and drawing context
    img = Image.new('RGB', (size, size), color=get_random_color())
    draw = ImageDraw.Draw(img)
    
    # Get or create initials
    if username:
        # Extract initials (up to 2 characters)
        initials = ''.join([name[0].upper() for name in username.split()[:2]])
        if not initials and username:
            initials = username[0].upper()
        if not initials:
            initials = "U"  # Default for empty usernames
    else:
        initials = "U"  # Default for None username
    
    # Limit to 2 characters
    initials = initials[:2]
    
    # Choose font size based on image size
    font_size = int(size * 0.4)
    try:
        # Try different fonts that might be available on the system
        font_names = ["arial.ttf", "Arial.ttf", "DejaVuSans.ttf", "calibri.ttf", "Calibri.ttf"]
        font = None
        
        for font_name in font_names:
            try:
                font = ImageFont.truetype(font_name, font_size)
                break
            except IOError:
                continue
        
        if font is None:
            font = ImageFont.load_default()
    except Exception:
        # Fallback to default font if nothing works
        font = ImageFont.load_default()
    
    # Calculate text position for centering
    try:
        # For newer PIL versions
        bbox = draw.textbbox((0, 0), initials, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
    except AttributeError:
        # For older PIL versions
        text_width, text_height = draw.textsize(initials, font=font)
    
    position = ((size - text_width) // 2, (size - text_height) // 2)
    
    # Draw the text
    draw.text(position, initials, font=font, fill="white")
    
    # Save image
    img.save(output_path)
    print(f"Generated profile placeholder: {output_path}")

def generate_event_placeholder(output_path, title=None, size=(800, 450)):
    """
    Generates a placeholder event logo with a calendar-like design.
    
    Args:
        output_path (str): Path to save the image
        title (str): Event title to display on the image
        size (tuple): Width and height of the image
    """
    width, height = size
    img = Image.new('RGB', size, color="#2c3e50")  # Dark blue background
    draw = ImageDraw.Draw(img)
    
    # Draw calendar icon
    margin = int(min(width, height) * 0.1)
    calendar_width = width - 2 * margin
    calendar_height = height - 2 * margin
    
    # Calendar header (red part)
    header_height = calendar_height // 4
    draw.rectangle(
        [(margin, margin), (margin + calendar_width, margin + header_height)],
        fill="#e74c3c"  # Red
    )
    
    # Calendar body (white part)
    draw.rectangle(
        [(margin, margin + header_height), (margin + calendar_width, margin + calendar_height)],
        fill="#ecf0f1"  # Light gray/white
    )
    
    # Calendar grid lines
    num_lines = 3
    line_spacing = (calendar_height - header_height) / (num_lines + 1)
    for i in range(1, num_lines + 1):
        y = margin + header_height + i * line_spacing
        draw.line([(margin, y), (margin + calendar_width, y)], fill="#bdc3c7", width=2)
    
    num_columns = 2
    column_spacing = calendar_width / (num_columns + 1)
    for i in range(1, num_columns + 1):
        x = margin + i * column_spacing
        draw.line(
            [(x, margin + header_height), (x, margin + calendar_height)],
            fill="#bdc3c7", width=2
        )
    
    # Add text if provided
    if title:
        # Truncate title if too long
        max_chars = 20
        display_title = title[:max_chars] + "..." if len(title) > max_chars else title
        
        try:
            # Try different fonts that might be available on the system
            font_names = ["arial.ttf", "Arial.ttf", "DejaVuSans.ttf", "calibri.ttf", "Calibri.ttf"]
            title_font = None
            
            for font_name in font_names:
                try:
                    title_font = ImageFont.truetype(font_name, int(header_height * 0.6))
                    break
                except IOError:
                    continue
            
            if title_font is None:
                title_font = ImageFont.load_default()
        except Exception:
            title_font = ImageFont.load_default()
        
        # Center text
        try:
            # For newer PIL versions
            bbox = draw.textbbox((0, 0), display_title, font=title_font)
            title_width = bbox[2] - bbox[0]
            title_height = bbox[3] - bbox[1]
        except AttributeError:
            # For older PIL versions
            title_width, title_height = draw.textsize(display_title, font=title_font)
        
        title_position = (
            margin + (calendar_width - title_width) // 2,
            margin + (header_height - title_height) // 2
        )
        
        draw.text(title_position, display_title, font=title_font, fill="white")
    
    # Save image
    img.save(output_path)
    print(f"Generated event placeholder: {output_path}")

def generate_news_placeholder(output_path, size=(1200, 800)):
    """
    Generates a placeholder news image with a newspaper-like design.
    
    Args:
        output_path (str): Path to save the image
        size (tuple): Width and height of the image
    """
    width, height = size
    img = Image.new('RGB', size, color="#f5f5f5")  # Light gray background
    draw = ImageDraw.Draw(img)
    
    # Draw a header area
    header_height = height // 5
    draw.rectangle([(0, 0), (width, header_height)], fill="#333333")
    
    # Draw title text
    try:
        # Try different fonts that might be available on the system
        font_names = ["arial.ttf", "Arial.ttf", "DejaVuSans.ttf", "calibri.ttf", "Calibri.ttf"]
        title_font = None
        
        for font_name in font_names:
            try:
                title_font = ImageFont.truetype(font_name, header_height // 2)
                break
            except IOError:
                continue
        
        if title_font is None:
            title_font = ImageFont.load_default()
    except Exception:
        title_font = ImageFont.load_default()
    
    news_title = "НОВОСТИ"
    try:
        # For newer PIL versions
        bbox = draw.textbbox((0, 0), news_title, font=title_font)
        title_width = bbox[2] - bbox[0]
        title_height = bbox[3] - bbox[1]
    except AttributeError:
        # For older PIL versions
        title_width, title_height = draw.textsize(news_title, font=title_font)
    
    title_position = ((width - title_width) // 2, (header_height - title_height) // 2)
    draw.text(title_position, news_title, font=title_font, fill="white")
    
    # Draw content columns
    columns = 3
    column_width = width // columns
    column_margin = width // 40
    
    for i in range(columns):
        col_x = i * column_width + column_margin
        col_width = column_width - 2 * column_margin
        
        # Column header
        col_header_height = (height - header_height) // 8
        draw.rectangle(
            [(col_x, header_height + column_margin), 
             (col_x + col_width, header_height + column_margin + col_header_height)],
            fill="#666666"
        )
        
        # Column content - draw text-like lines
        num_lines = 10
        line_height = (height - header_height - col_header_height - 3 * column_margin) / (num_lines * 2)
        
        for j in range(num_lines):
            line_y = header_height + column_margin + col_header_height + column_margin + j * line_height * 2
            line_width = random.randint(int(col_width * 0.7), col_width)
            draw.rectangle(
                [(col_x, line_y), (col_x + line_width, line_y + line_height * 0.7)],
                fill="#aaaaaa"
            )
    
    # Save image
    img.save(output_path)
    print(f"Generated news placeholder: {output_path}")

def generate_achievement_placeholder(output_path, achievement_type=None, size=200):
    """
    Generates a placeholder achievement icon with a trophy or badge design.
    
    Args:
        output_path (str): Path to save the image
        achievement_type (str): Type of achievement (e.g., 'participation', 'organizer')
        size (int): Size of the image in pixels
    """
    img = Image.new('RGB', (size, size), color=get_random_color(pastel=True))
    draw = ImageDraw.Draw(img)
    
    # Determine achievement type color and symbol
    if achievement_type == 'organizer':
        main_color = "#3498db"  # Blue
        symbol = "🏆"  # Trophy
    elif achievement_type == 'participation':
        main_color = "#2ecc71"  # Green
        symbol = "🎖️"  # Medal
    elif achievement_type == 'special':
        main_color = "#9b59b6"  # Purple
        symbol = "🌟"  # Star
    else:
        main_color = "#f1c40f"  # Gold/Yellow
        symbol = "🏅"  # Sports medal
    
    # Draw circular background
    margin = int(size * 0.1)
    diameter = size - 2 * margin
    draw.ellipse([(margin, margin), (margin + diameter, margin + diameter)], fill=main_color)
    
    # Draw symbol (we'll use shapes since PIL doesn't handle emojis well)
    if symbol in ["🏆", "🎖️", "🏅"]:  # Trophy or medal
        # Draw a trophy cup shape
        cup_width = diameter * 0.6
        cup_height = diameter * 0.5
        cup_top = margin + diameter * 0.2
        cup_left = margin + (diameter - cup_width) / 2
        
        # Cup body
        draw.rectangle(
            [(cup_left, cup_top), (cup_left + cup_width, cup_top + cup_height)],
            fill="white"
        )
        
        # Cup handles
        handle_width = cup_width * 0.2
        draw.ellipse(
            [(cup_left - handle_width, cup_top + cup_height * 0.2),
             (cup_left, cup_top + cup_height * 0.8)],
            fill="white"
        )
        draw.ellipse(
            [(cup_left + cup_width, cup_top + cup_height * 0.2),
             (cup_left + cup_width + handle_width, cup_top + cup_height * 0.8)],
            fill="white"
        )
        
        # Cup base
        base_width = cup_width * 0.4
        base_height = cup_height * 0.3
        base_left = cup_left + (cup_width - base_width) / 2
        draw.rectangle(
            [(base_left, cup_top + cup_height),
             (base_left + base_width, cup_top + cup_height + base_height)],
            fill="white"
        )
    elif symbol == "🌟":  # Star
        # Draw a star
        center_x = margin + diameter / 2
        center_y = margin + diameter / 2
        radius = diameter / 2
        points = 5
        inner_radius = radius * 0.4
        
        star_points = []
        for i in range(points * 2):
            angle = math.pi * i / points - math.pi / 2
            r = inner_radius if i % 2 else radius
            x = center_x + r * math.cos(angle)
            y = center_y + r * math.sin(angle)
            star_points.append((x, y))
        
        draw.polygon(star_points, fill="white")
    
    # Save image
    img.save(output_path)
    print(f"Generated achievement placeholder: {output_path}")

# Utility functions to get placeholder paths
def ensure_placeholder_directories():
    """
    Ensures all necessary directories for placeholders exist
    
    Returns:
        list: List of directory paths for different image types
    """
    # Get the app's static directory from current app context
    static_img_dir = os.path.join(current_app.root_path, 'static', 'img')

    # Create directories if they don't exist
    dirs = [
        os.path.join(static_img_dir, 'profile_pics'),
        os.path.join(static_img_dir, 'event_logos'),
        os.path.join(static_img_dir, 'news_images'),
        os.path.join(static_img_dir, 'achievement_icons')
    ]
    
    for directory in dirs:
        if not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)
            print(f"Created directory: {directory}")
    
    return dirs

def get_profile_placeholder():
    """
    Returns the path to the default profile placeholder
    
    Returns:
        str: URL path for the profile placeholder image
    """
    return os.path.join('/static', 'img', 'profile_pics', 'default.jpg')

def get_event_placeholder():
    """
    Returns the path to the default event placeholder
    
    Returns:
        str: URL path for the event placeholder image
    """
    return os.path.join('/static', 'img', 'event_logos', 'default_event.jpg')

def get_news_placeholder():
    """
    Returns the path to the default news placeholder
    
    Returns:
        str: URL path for the news placeholder image
    """
    return os.path.join('/static', 'img', 'news_images', 'default_news.jpg')

def get_achievement_placeholder():
    """
    Returns the path to the default achievement placeholder
    
    Returns:
        str: URL path for the achievement placeholder image
    """
    return os.path.join('/static', 'img', 'achievement_icons', 'default_achievement.png')

def generate_default_placeholders():
    """
    Generates default placeholder images for all required types
    
    Returns:
        int: Number of placeholder images generated
    """
    # Ensure directories exist
    dirs = ensure_placeholder_directories()
    count = 0
    
    # Define default filenames (absolute paths)
    profile_pic_path = os.path.join(current_app.root_path, 'static', 'img', 'profile_pics', 'default.jpg')
    event_logo_path = os.path.join(current_app.root_path, 'static', 'img', 'event_logos', 'default_event.jpg')
    news_image_path = os.path.join(current_app.root_path, 'static', 'img', 'news_images', 'default_news.jpg')
    achievement_path = os.path.join(current_app.root_path, 'static', 'img', 'achievement_icons', 'default_achievement.png')
    
    # Generate placeholders if they don't exist
    if not os.path.exists(profile_pic_path):
        generate_profile_placeholder(profile_pic_path, username="User")
        count += 1
    
    if not os.path.exists(event_logo_path):
        generate_event_placeholder(event_logo_path, title="Мероприятие")
        count += 1
    
    if not os.path.exists(news_image_path):
        generate_news_placeholder(news_image_path)
        count += 1
    
    if not os.path.exists(achievement_path):
        generate_achievement_placeholder(achievement_path)
        count += 1
    
    # Generate additional achievement placeholders
    organizer_path = os.path.join(current_app.root_path, 'static', 'img', 'achievement_icons', 'achievement_organizer.png')
    participation_path = os.path.join(current_app.root_path, 'static', 'img', 'achievement_icons', 'achievement_participation.png')
    special_path = os.path.join(current_app.root_path, 'static', 'img', 'achievement_icons', 'achievement_special.png')
    
    if not os.path.exists(organizer_path):
        generate_achievement_placeholder(organizer_path, achievement_type='organizer')
        count += 1
    
    if not os.path.exists(participation_path):
        generate_achievement_placeholder(participation_path, achievement_type='participation')
        count += 1
    
    if not os.path.exists(special_path):
        generate_achievement_placeholder(special_path, achievement_type='special')
        count += 1
    
    return count 