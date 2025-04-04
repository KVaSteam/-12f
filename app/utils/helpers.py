import os
import secrets
from PIL import Image
from flask import current_app, flash, redirect, url_for, abort
from functools import wraps
from flask_login import current_user

def save_image(image_data, folder, filename=None):
    """
    Save the image data to the specified folder and return the filename
    
    Args:
        image_data: The image data to save (can be None)
        folder: The folder to save the image to
        filename: The filename to use (will be generated if None)
        
    Returns:
        str: The filename of the saved image
    """
    if not image_data:
        # Return appropriate placeholder based on folder
        from app.utils.placeholders import get_profile_placeholder, get_event_placeholder, get_news_placeholder, get_achievement_placeholder
        
        if folder == 'profile_pics':
            return get_profile_placeholder()
        elif folder == 'event_logos':
            return get_event_placeholder()
        elif folder == 'news_images':
            return get_news_placeholder()
        elif folder == 'achievement_icons' or folder == 'event_achievement_icons':
            return get_achievement_placeholder()
        else:
            # Default to profile placeholder
            return get_profile_placeholder()
    
    # Generate random filename if not provided
    if not filename:
        import secrets
        filename = secrets.token_hex(16) + '.jpg'
    
    # Ensure the directory exists
    directory = os.path.join(current_app.root_path, 'static', 'img', folder)
    if not os.path.exists(directory):
        os.makedirs(directory)
    
    # Resize the image to save space and maintain consistency
    from io import BytesIO
    
    image = Image.open(BytesIO(image_data))
    
    # Determine max dimensions based on image type
    if folder == 'profile_pics':
        output_size = (200, 200)  # Profile pics are square
    elif folder == 'event_logos':
        output_size = (800, 450)  # 16:9 aspect ratio for events
    elif folder == 'news_images':
        output_size = (1200, 800)  # Larger images for news
    elif folder == 'achievement_icons' or folder == 'event_achievement_icons':
        output_size = (200, 200)  # Square for achievement icons
    else:
        output_size = (400, 400)  # Default
    
    # Resize image while preserving aspect ratio
    image.thumbnail(output_size)
    
    # Save the image
    filepath = os.path.join(directory, filename)
    image.save(filepath, quality=85, optimize=True)
    
    # Return the relative path for database storage
    return os.path.join('/static', 'img', folder, filename)

def admin_required(f):
    """
    Декоратор для проверки, является ли пользователь администратором
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_admin():
            flash('У вас нет прав для доступа к этой странице', 'danger')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function

def get_or_create_tag(name):
    """
    Получает существующий тег или создает новый по указанному имени
    """
    from app import db
    from app.models import Tag
    
    tag = Tag.query.filter_by(name=name).first()
    if not tag:
        tag = Tag(name=name)
        db.session.add(tag)
        db.session.commit()
    
    return tag

def check_and_award_achievements(user):
    """
    Проверяет условия для получения достижений и 
    выдает их пользователю при выполнении условий
    """
    from app import db
    from app.models import Achievement, EventApplication, Event
    
    # Получаем все достижения
    all_achievements = Achievement.query.all()
    user_achievements = set(user.achievements)
    awarded = False
    
    # Проверяем каждое достижение
    for achievement in all_achievements:
        # Пропускаем, если уже получено
        if achievement in user_achievements:
            continue
        
        # Проверяем различные условия для получения достижений
        
        # Пример: достижение за регистрацию на первое мероприятие
        if achievement.condition == 'first_event_registration':
            applications_count = EventApplication.query.filter_by(user_id=user.id).count()
            if applications_count == 1:
                user.achievements.append(achievement)
                awarded = True
        
        # Пример: достижение за регистрацию на 5 мероприятий
        elif achievement.condition == 'five_events_registration':
            applications_count = EventApplication.query.filter_by(user_id=user.id).count()
            if applications_count >= 5:
                user.achievements.append(achievement)
                awarded = True
        
        # Пример: достижение для организатора за первое мероприятие
        elif achievement.condition == 'first_event_created' and user.is_organizer():
            events_count = Event.query.filter_by(organizer_id=user.id).count()
            if events_count == 1:
                user.achievements.append(achievement)
                awarded = True
        
        # Другие условия можно добавить по аналогии
    
    # Сохраняем изменения в БД, если были выданы достижения
    if awarded:
        db.session.commit()
    
    return awarded

def generate_qr_code(url, size=200):
    """
    Генерирует QR-код для указанного URL
    
    Args:
        url: URL адрес, который будет закодирован в QR-код
        size: Размер QR-кода в пикселях (по умолчанию 200)
        
    Returns:
        str: Base64 представление QR-кода для вставки в HTML
    """
    import qrcode
    import base64
    from io import BytesIO
    
    # Создаем QR-код
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=4,
    )
    qr.add_data(url)
    qr.make(fit=True)
    
    # Создаем изображение
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Преобразуем изображение в base64 для вставки в HTML
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode('utf-8')
    
    return f"data:image/png;base64,{img_str}" 