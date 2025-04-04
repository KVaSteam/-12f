from datetime import datetime
from app import db
from enum import Enum

class NotificationType(Enum):
    EVENT_APPLICATION = 'event_application'  # Новая заявка на мероприятие
    APPLICATION_APPROVED = 'application_approved'  # Заявка одобрена
    APPLICATION_REJECTED = 'application_rejected'  # Заявка отклонена
    EVENT_APPROVED = 'event_approved'  # Мероприятие одобрено
    EVENT_REJECTED = 'event_rejected'  # Мероприятие отклонено
    ACHIEVEMENT_EARNED = 'achievement_earned'  # Получено достижение
    EVENT_REMINDER = 'event_reminder'  # Напоминание о мероприятии
    EVENT_COMPLETED = 'event_completed'  # Мероприятие завершено

class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    content = db.Column(db.String(255), nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    type = db.Column(db.String(50), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    related_id = db.Column(db.Integer, nullable=True)  # ID связанного объекта (события, заявки и т.д.)
    
    # Отношения с моделью User
    user = db.relationship('User', backref=db.backref('notifications', lazy='dynamic'))
    
    def __repr__(self):
        return f"Notification('{self.user_id}', '{self.type}', '{self.content}')" 