from datetime import datetime
from flask import current_app
from flask_login import UserMixin
from app import db, login_manager
from enum import Enum
from app.models.event import EventAchievement  # Добавляем импорт EventAchievement
from app.models.achievement import OrganizerAchievement  # Добавляем импорт OrganizerAchievement
from app.models.notification import Notification  # Добавляем импорт Notification

class UserRole(Enum):
    PARTICIPANT = 'participant'
    ORGANIZER = 'organizer'
    ADMIN = 'admin'

# Таблица для отслеживания полученных достижений пользователя
user_achievements = db.Table('user_achievements',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('achievement_id', db.Integer, db.ForeignKey('achievement.id'), primary_key=True),
    db.Column('earned_at', db.DateTime, default=datetime.utcnow)
)

# Таблица для заявок на участие в мероприятиях
class EventApplication(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'), nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, approved, rejected
    points = db.Column(db.Integer, default=0)  # Очки, полученные участником
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = db.relationship('User', back_populates='applications')
    event = db.relationship('Event', back_populates='applications')
    
    def __repr__(self):
        return f"EventApplication('{self.user_id}', '{self.event_id}', '{self.status}')"

# Таблица для отслеживания достижений пользователя на мероприятиях
class UserEventAchievement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    achievement_id = db.Column(db.Integer, db.ForeignKey('event_achievement.id'), nullable=False)
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'), nullable=True)
    date_earned = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Отношения
    user = db.relationship('User', back_populates='event_achievements')
    achievement = db.relationship('EventAchievement', back_populates='users')
    event = db.relationship('Event', backref=db.backref('user_achievements', lazy='dynamic'))
    
    def __repr__(self):
        return f"UserEventAchievement('{self.user_id}', '{self.achievement_id}')"

# Таблица для отслеживания достижений организаторов
class UserOrganizerAchievement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    achievement_id = db.Column(db.Integer, db.ForeignKey('organizer_achievement.id'), nullable=False)
    date_earned = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Отношения
    user = db.relationship('User', back_populates='organizer_achievements')
    achievement = db.relationship('OrganizerAchievement', back_populates='users')
    
    def __repr__(self):
        return f"UserOrganizerAchievement('{self.user_id}', '{self.achievement_id}')"

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    role = db.Column(db.String(20), default=UserRole.PARTICIPANT.value)
    profile_image = db.Column(db.String(20), default='default.jpg')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Отношения с другими моделями
    organized_events = db.relationship('Event', back_populates='organizer')
    applications = db.relationship('EventApplication', back_populates='user')
    achievements = db.relationship('Achievement', secondary=user_achievements, 
                                   backref=db.backref('users', lazy='dynamic'))
    event_achievements = db.relationship('UserEventAchievement', back_populates='user')
    organizer_achievements = db.relationship('UserOrganizerAchievement', back_populates='user')
    
    def __repr__(self):
        return f"User('{self.username}', '{self.email}', '{self.role}')"
    
    def is_admin(self):
        return self.role == UserRole.ADMIN.value
        
    def is_organizer(self):
        return self.role == UserRole.ORGANIZER.value or self.role == UserRole.ADMIN.value
        
    def total_points(self):
        """Подсчет общего количества очков пользователя"""
        # Получаем очки за участие в мероприятиях
        event_points = db.session.query(db.func.sum(EventApplication.points)).\
            filter(EventApplication.user_id == self.id,
                   EventApplication.status == 'approved').scalar() or 0
        
        # Получаем очки за достижения мероприятий
        achievement_points = db.session.query(db.func.sum(EventAchievement.points)).\
            join(UserEventAchievement, UserEventAchievement.achievement_id == EventAchievement.id).\
            filter(UserEventAchievement.user_id == self.id).scalar() or 0
        
        # Получаем очки за достижения организаторов
        organizer_achievement_points = db.session.query(db.func.sum(OrganizerAchievement.points)).\
            join(UserOrganizerAchievement, UserOrganizerAchievement.achievement_id == OrganizerAchievement.id).\
            filter(UserOrganizerAchievement.user_id == self.id).scalar() or 0
        
        return event_points + achievement_points + organizer_achievement_points
    
    def count_completed_events(self):
        """Подсчет количества завершенных мероприятий с хотя бы одним участником"""
        from app.models.event import Event, EventStatus
        from sqlalchemy import func
        
        # Запрос количества завершенных мероприятий
        completed_events_count = db.session.query(func.count(Event.id)).\
            filter(Event.organizer_id == self.id,
                   Event.status == EventStatus.COMPLETED.value).\
            join(EventApplication).\
            filter(EventApplication.status == 'approved').\
            group_by(Event.id).\
            having(func.count(EventApplication.id) >= 1).\
            count()
        
        return completed_events_count

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id)) 