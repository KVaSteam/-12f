from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, current_user, logout_user, login_required
from app import db, bcrypt
from app.models import User, UserRole
from app.utils.forms import RegistrationForm, LoginForm
from app.utils.validators import is_russian_email

auth = Blueprint('auth', __name__)

@auth.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        # Проверка на российскую почту
        if not is_russian_email(form.email.data):
            flash('Регистрация возможна только с российскими почтовыми сервисами', 'danger')
            return render_template('auth/register.html', title='Регистрация', form=form)
        
        # Хеширование пароля и создание пользователя
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(
            username=form.username.data,
            email=form.email.data,
            password=hashed_password,
            role=UserRole.PARTICIPANT.value if form.role.data == 'participant' else UserRole.ORGANIZER.value
        )
        
        db.session.add(user)
        db.session.commit()
        
        flash('Ваш аккаунт создан! Теперь вы можете войти в систему', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/register.html', title='Регистрация', form=form)

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('main.index'))
        else:
            flash('Ошибка входа. Проверьте адрес электронной почты и пароль', 'danger')
    
    return render_template('auth/login.html', title='Вход', form=form)

@auth.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('main.index')) 