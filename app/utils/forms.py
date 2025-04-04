from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, PasswordField, SubmitField, BooleanField, TextAreaField, SelectField, DateTimeLocalField, IntegerField, SelectMultipleField, HiddenField, RadioField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError, Optional, NumberRange
from app.models import User, EventFormat
from app.utils.validators import is_russian_email
from flask_login import current_user
from datetime import datetime
from app.models.achievement import AchievementConditionType

class RegistrationForm(FlaskForm):
    username = StringField('Имя пользователя', validators=[
        DataRequired(message='Это поле обязательно'), 
        Length(min=3, max=20, message='Имя должно содержать от 3 до 20 символов')
    ])
    email = StringField('Email', validators=[
        DataRequired(message='Это поле обязательно'), 
        Email(message='Введите корректный email адрес')
    ])
    password = PasswordField('Пароль', validators=[
        DataRequired(message='Это поле обязательно'),
        Length(min=6, message='Пароль должен содержать не менее 6 символов')
    ])
    confirm_password = PasswordField('Подтверждение пароля', validators=[
        DataRequired(message='Это поле обязательно'),
        EqualTo('password', message='Пароли должны совпадать')
    ])
    role = SelectField('Тип аккаунта', choices=[
        ('participant', 'Участник'),
        ('organizer', 'Организатор')
    ])
    submit = SubmitField('Зарегистрироваться')
    
    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Это имя пользователя уже занято. Пожалуйста, выберите другое.')
    
    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Этот email уже зарегистрирован. Пожалуйста, используйте другой.')
        
        if not is_russian_email(email.data):
            raise ValidationError('Разрешена регистрация только с российскими почтовыми сервисами.')

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[
        DataRequired(message='Это поле обязательно'), 
        Email(message='Введите корректный email адрес')
    ])
    password = PasswordField('Пароль', validators=[
        DataRequired(message='Это поле обязательно')
    ])
    remember = BooleanField('Запомнить меня')
    submit = SubmitField('Войти')

class UpdateProfileForm(FlaskForm):
    username = StringField('Имя пользователя', validators=[
        DataRequired(message='Это поле обязательно'), 
        Length(min=3, max=20, message='Имя должно содержать от 3 до 20 символов')
    ])
    password = PasswordField('Новый пароль (оставьте пустым, чтобы не менять)', validators=[
        Optional(),
        Length(min=6, message='Пароль должен содержать не менее 6 символов')
    ])
    confirm_password = PasswordField('Подтверждение нового пароля', validators=[
        EqualTo('password', message='Пароли должны совпадать')
    ])
    profile_image = FileField('Аватар', validators=[
        FileAllowed(['jpg', 'png', 'jpeg', 'gif'], 'Только изображения!')
    ])
    submit = SubmitField('Обновить')
    
    def validate_username(self, username):
        if username.data != current_user.username:
            user = User.query.filter_by(username=username.data).first()
            if user:
                raise ValidationError('Это имя пользователя уже занято. Пожалуйста, выберите другое.')

class EventForm(FlaskForm):
    title = StringField('Название мероприятия', validators=[
        DataRequired(message='Это поле обязательно'), 
        Length(max=100, message='Название не должно превышать 100 символов')
    ])
    description = TextAreaField('Описание', validators=[
        DataRequired(message='Это поле обязательно')
    ])
    start_datetime = DateTimeLocalField('Дата и время начала', 
                                      format='%Y-%m-%dT%H:%M', 
                                      validators=[DataRequired(message='Это поле обязательно')])
    end_datetime = DateTimeLocalField('Дата и время окончания', 
                                    format='%Y-%m-%dT%H:%M', 
                                    validators=[DataRequired(message='Это поле обязательно')])
    location = StringField('Место проведения', validators=[
        DataRequired(message='Это поле обязательно'), 
        Length(max=200, message='Адрес не должен превышать 200 символов')
    ])
    format = SelectField('Формат мероприятия', choices=[
        (EventFormat.OFFLINE.value, 'Офлайн'),
        (EventFormat.ONLINE.value, 'Онлайн'),
        (EventFormat.HYBRID.value, 'Гибридный')
    ])
    tags = SelectMultipleField('Теги', coerce=int, validators=[
        DataRequired(message='Выберите хотя бы один тег')
    ])
    default_points = IntegerField('Очки за участие (по умолчанию)', default=10, validators=[
        DataRequired(message='Это поле обязательно')
    ])
    max_participants = IntegerField('Максимальное количество участников', default=0, validators=[
        NumberRange(min=0, message='Значение должно быть положительным (0 - без ограничений)')
    ])
    logo = FileField('Логотип мероприятия', validators=[
        FileAllowed(['jpg', 'png', 'jpeg', 'gif'], 'Только изображения!')
    ])
    submit = SubmitField('Сохранить')
    
    def validate_end_datetime(self, end_datetime):
        if end_datetime.data <= self.start_datetime.data:
            raise ValidationError('Время окончания должно быть позже времени начала.')
        
    def validate_start_datetime(self, start_datetime):
        if start_datetime.data < datetime.now():
            raise ValidationError('Нельзя создать мероприятие в прошлом.')

class NewsForm(FlaskForm):
    title = StringField('Заголовок', validators=[
        DataRequired(message='Это поле обязательно'), 
        Length(max=100, message='Заголовок не должен превышать 100 символов')
    ])
    content = TextAreaField('Содержание', validators=[
        DataRequired(message='Это поле обязательно')
    ])
    image = FileField('Изображение', validators=[
        FileAllowed(['jpg', 'png', 'jpeg', 'gif'], 'Только изображения!')
    ])
    submit = SubmitField('Сохранить')

class AchievementForm(FlaskForm):
    name = StringField('Название достижения', validators=[
        DataRequired(message='Это поле обязательно'), 
        Length(max=100, message='Название не должно превышать 100 символов')
    ])
    description = TextAreaField('Описание', validators=[
        DataRequired(message='Это поле обязательно')
    ])
    condition = StringField('Условие получения', validators=[
        Length(max=255, message='Условие не должно превышать 255 символов')
    ])
    points = IntegerField('Очки', default=10, validators=[
        DataRequired(message='Это поле обязательно')
    ])
    icon = FileField('Иконка', validators=[
        FileAllowed(['jpg', 'png', 'jpeg', 'gif'], 'Только изображения!')
    ])
    submit = SubmitField('Сохранить')

class ApplicationActionForm(FlaskForm):
    action = HiddenField('Действие')
    submit = SubmitField('Применить')

class EventAchievementForm(FlaskForm):
    name = StringField('Название достижения', validators=[
        DataRequired(message='Это поле обязательно'), 
        Length(max=100, message='Название не должно превышать 100 символов')
    ])
    description = TextAreaField('Описание', validators=[
        Length(max=500, message='Описание не должно превышать 500 символов')
    ])
    points = IntegerField('Очки за достижение', default=10, validators=[
        DataRequired(message='Это поле обязательно')
    ])
    icon = FileField('Иконка достижения', validators=[
        FileAllowed(['jpg', 'png', 'jpeg', 'gif'], 'Только изображения!')
    ])
    submit = SubmitField('Сохранить')

class EventReviewForm(FlaskForm):
    rating = RadioField('Оценка мероприятия', 
                        choices=[(5, '5'), (4, '4'), (3, '3'), (2, '2'), (1, '1')],
                        validators=[DataRequired()], coerce=int)
    comment = TextAreaField('Комментарий', validators=[
        Length(max=1000, message='Комментарий не должен превышать 1000 символов')
    ])
    submit = SubmitField('Отправить отзыв')

class EventFilterForm(FlaskForm):
    start_date = DateTimeLocalField('Дата начала', format='%Y-%m-%dT%H:%M', validators=[Optional()])
    end_date = DateTimeLocalField('Дата окончания', format='%Y-%m-%dT%H:%M', validators=[Optional()])
    event_format = SelectField('Формат', choices=[
        ('', 'Все форматы'),
        (EventFormat.OFFLINE.value, 'Офлайн'),
        (EventFormat.ONLINE.value, 'Онлайн'),
        (EventFormat.HYBRID.value, 'Гибридный')
    ], validators=[Optional()])
    status = SelectField('Статус', choices=[
        ('', 'Все статусы'),
        ('active', 'Активные'),
        ('completed', 'Завершенные')
    ], validators=[Optional()])
    tags = SelectMultipleField('Теги', coerce=int, validators=[Optional()])
    submit = SubmitField('Применить фильтры')

class OrganizerAchievementForm(FlaskForm):
    name = StringField('Название достижения', validators=[
        DataRequired(message='Это поле обязательно'), 
        Length(max=100, message='Название не должно превышать 100 символов')
    ])
    description = TextAreaField('Описание', validators=[
        DataRequired(message='Это поле обязательно'),
        Length(max=500, message='Описание не должно превышать 500 символов')
    ])
    condition_type = SelectField('Тип условия', choices=[
        (AchievementConditionType.PARTICIPANTS_COUNT.value, 'Количество участников в мероприятии'),
        (AchievementConditionType.EVENTS_COUNT.value, 'Количество проведенных мероприятий')
    ], validators=[DataRequired(message='Это поле обязательно')])
    condition_value = IntegerField('Необходимое значение', validators=[
        DataRequired(message='Это поле обязательно'),
        NumberRange(min=1, message='Значение должно быть не менее 1')
    ])
    points = IntegerField('Очки за достижение', default=10, validators=[
        DataRequired(message='Это поле обязательно'),
        NumberRange(min=1, message='Должно быть не менее 1 очка')
    ])
    icon = FileField('Иконка достижения', validators=[
        FileAllowed(['jpg', 'png', 'jpeg', 'gif'], 'Только изображения!')
    ])
    submit = SubmitField('Сохранить')

class EventApplicationForm(FlaskForm):
    submit = SubmitField('Подать заявку') 