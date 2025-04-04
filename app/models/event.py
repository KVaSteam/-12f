from datetime import datetime
from app import db
from enum import Enum
from sqlalchemy import func

class EventStatus(Enum):
    PENDING = 'pending'
    APPROVED = 'approved'
    REJECTED = 'rejected'
    CANCELED = 'canceled'
    COMPLETED = 'completed'

class EventFormat(Enum):
    ONLINE = 'online'
    OFFLINE = 'offline'
    HYBRID = 'hybrid'

# Таблица для связи события и тегов
event_tags = db.Table('event_tags',
    db.Column('event_id', db.Integer, db.ForeignKey('event.id'), primary_key=True),
    db.Column('tag_id', db.Integer, db.ForeignKey('tag.id'), primary_key=True)
)

class Tag(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    
    def __repr__(self):
        return f"Tag('{self.name}')"

class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    start_datetime = db.Column(db.DateTime, nullable=False)
    end_datetime = db.Column(db.DateTime, nullable=False)
    location = db.Column(db.String(200))
    format = db.Column(db.String(20), default=EventFormat.OFFLINE.value)
    logo = db.Column(db.String(100), default='default_event.jpg')
    status = db.Column(db.String(20), default=EventStatus.PENDING.value)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    default_points = db.Column(db.Integer, default=10)  # Очки по умолчанию для участников
    max_participants = db.Column(db.Integer, default=0)  # Максимальное количество участников (0 - без ограничений)
    
    # Внешние ключи
    organizer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Отношения
    organizer = db.relationship('User', back_populates='organized_events')
    applications = db.relationship('EventApplication', back_populates='event', cascade='all, delete-orphan')
    tags = db.relationship('Tag', secondary=event_tags, backref=db.backref('events', lazy='dynamic'))
    achievements = db.relationship('EventAchievement', back_populates='event', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f"Event('{self.title}', '{self.start_datetime}', '{self.status}')"
    
    @property
    def is_past(self):
        return datetime.utcnow() > self.end_datetime
    
    @property
    def is_active(self):
        return self.status == EventStatus.APPROVED.value and not self.is_past
        
    @property
    def is_completed(self):
        return self.status == EventStatus.COMPLETED.value
        
    def participants_count(self):
        """Возвращает количество одобренных участников мероприятия"""
        # Используем локальный импорт для избежания циклических зависимостей
        from app.models.user import EventApplication
        
        count = db.session.query(func.count(EventApplication.id)).\
            filter(EventApplication.event_id == self.id,
                   EventApplication.status == 'approved').\
            scalar() or 0
        
        return count
        
    def available_spots(self):
        """Возвращает количество доступных мест, или None если мест не ограничено"""
        if self.max_participants <= 0:  # Если 0 или меньше - мест не ограничено
            return None
        
        # Вычисляем сколько мест осталось
        approved_count = self.participants_count()
        return max(0, self.max_participants - approved_count)
        
    def average_rating(self):
        """Возвращает средний рейтинг мероприятия на основе отзывов"""
        avg = db.session.query(func.avg(EventReview.rating)).\
            filter(EventReview.event_id == self.id).\
            scalar() or 0
        
        return avg

class EventAchievement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    points = db.Column(db.Integer, default=10)
    icon = db.Column(db.String(100), default='default_achievement.png')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Внешние ключи
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'), nullable=False)
    
    # Отношения
    event = db.relationship('Event', back_populates='achievements')
    users = db.relationship('UserEventAchievement', back_populates='achievement')
    
    def __repr__(self):
        return f"EventAchievement('{self.name}', '{self.event_id}', {self.points} points)"

class EventReview(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    rating = db.Column(db.Integer, nullable=False)  # Рейтинг от 1 до 5
    comment = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Внешние ключи
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Отношения
    event = db.relationship('Event', backref=db.backref('reviews', lazy='dynamic'))
    user = db.relationship('User', backref=db.backref('event_reviews', lazy='dynamic'))
    
    def __repr__(self):
        return f"EventReview('{self.user_id}', '{self.event_id}', {self.rating})" 