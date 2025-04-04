from app import db
from datetime import datetime

class News(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    image = db.Column(db.String(100), default='default_news.jpg')
    published_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Внешние ключи
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Отношения
    author = db.relationship('User', backref='authored_news')
    
    def __repr__(self):
        return f"News('{self.title}', '{self.published_at}')"
        
    # Псевдоним для совместимости с шаблонами
    @property
    def image_file(self):
        return self.image 