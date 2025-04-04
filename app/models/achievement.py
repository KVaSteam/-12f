from app import db
from datetime import datetime
from enum import Enum

class AchievementConditionType(Enum):
    PARTICIPANTS_COUNT = 'participants_count'  # Достижение за количество участников в одном мероприятии
    EVENTS_COUNT = 'events_count'  # Достижение за количество проведенных мероприятий

class Achievement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    icon = db.Column(db.String(100), default='default_achievement.png')
    condition = db.Column(db.String(255))  # Условие получения (может быть описательным или кодом)
    points = db.Column(db.Integer, default=10)  # Количество очков за достижение
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"Achievement('{self.name}', '{self.points} points')"

class OrganizerAchievement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    icon = db.Column(db.String(100), default='default_achievement.png')
    points = db.Column(db.Integer, default=10)  # Количество очков за достижение
    
    # Тип условия и необходимое значение для выполнения
    condition_type = db.Column(db.String(50), nullable=False)  # Тип условия из enum AchievementConditionType
    condition_value = db.Column(db.Integer, default=1)  # Необходимое значение для выполнения условия
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Отношения
    users = db.relationship('UserOrganizerAchievement', back_populates='achievement')
    
    def __repr__(self):
        return f"OrganizerAchievement('{self.name}', '{self.condition_type}', {self.condition_value}, {self.points} points)" 