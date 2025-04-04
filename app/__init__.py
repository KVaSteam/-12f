import os
import logging
import click
from flask import Flask, current_app
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from flask_migrate import Migrate

# Initialize extensions
db = SQLAlchemy()
bcrypt = Bcrypt()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message_category = 'info'
csrf = CSRFProtect()
migrate = Migrate()

# Configure logger
logger = logging.getLogger(__name__)

def create_app():
    app = Flask(__name__)
    
    # Application configuration
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev_key_12345')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///site.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Initialize extensions with app
    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    migrate.init_app(app, db)
    
    # Create upload folders
    with app.app_context():
        upload_folder = os.path.join(app.static_folder, 'img')
        if not os.path.exists(upload_folder):
            os.makedirs(upload_folder)
            logger.info(f"Создана папка загрузки: {upload_folder}")
            
        # Create directories for different image types
        for img_dir in ['profile_pics', 'news_images', 'event_logos', 'achievement_icons']:
            dir_path = os.path.join(upload_folder, img_dir)
            if not os.path.exists(dir_path):
                os.makedirs(dir_path)
                logger.info(f"Создана директория: {dir_path}")
        
        # Initialize placeholder images
        try:
            from app.utils.placeholder import generate_default_placeholders
            generate_default_placeholders(app.static_folder)
            logger.info("Созданы изображения-заполнители")
        except Exception as e:
            logger.error(f"Ошибка при создании изображений-заполнителей: {str(e)}")
    
    # Register blueprints
    from app.routes.main import main
    from app.routes.auth import auth
    from app.routes.events import events
    from app.routes.profile import profile
    from app.routes.admin import admin
    from app.routes.notifications import notifications
    from app.routes.chatbot import chatbot
    
    app.register_blueprint(main)
    app.register_blueprint(auth, url_prefix='/auth')
    app.register_blueprint(events, url_prefix='/event')
    app.register_blueprint(profile, url_prefix='/profile')
    app.register_blueprint(admin, url_prefix='/admin')
    app.register_blueprint(notifications)
    app.register_blueprint(chatbot)
    
    # Register CLI commands
    @app.cli.command('generate-placeholders')
    def generate_placeholders_command():
        """Create placeholder images for the application."""
        from app.utils.placeholder import generate_default_placeholders
        generate_default_placeholders(app.static_folder)
        click.echo('Созданы изображения-заполнители.')
    
    # Add filter to convert newlines to HTML <br> tags
    @app.template_filter('nl2br')
    def nl2br_filter(s):
        if s is None:
            return ""
        return s.replace('\n', '<br>')
    
    return app

from app.models.user import User

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
