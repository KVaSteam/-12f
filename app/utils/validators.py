from flask import current_app

def is_russian_email(email):
    """
    Проверяет, принадлежит ли email к одному из разрешенных российских почтовых сервисов
    """
    if not email:
        return False
    
    try:
        domain = email.split('@')[1].lower()
        return domain in current_app.config['ALLOWED_EMAIL_DOMAINS']
    except (IndexError, AttributeError):
        return False 