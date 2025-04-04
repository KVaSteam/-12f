from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import current_user, login_required
from app import db, bcrypt
from app.models import User, Event, EventApplication, Achievement
from app.utils.forms import UpdateProfileForm
from app.utils.helpers import save_image
from app.models.user import UserEventAchievement
from sqlalchemy.sql import func, distinct

profile = Blueprint('profile', __name__)

@profile.route('/profile', methods=['GET', 'POST'])
@login_required
def user_profile():
    # Перенаправляем на просмотр своего профиля
    return redirect(url_for('profile.view_profile', user_id=current_user.id))
    
@profile.route('/profile/update', methods=['GET', 'POST'])
@login_required
def update_profile():
    form = UpdateProfileForm()
    
    if form.validate_on_submit():
        # Обновляем данные профиля пользователя
        current_user.username = form.username.data
        
        # Если указан новый пароль, обновляем его
        if form.password.data:
            current_user.password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        
        # Если загружена новая аватарка, сохраняем ее
        if form.profile_image.data:
            current_user.profile_image = save_image(form.profile_image.data, 'profile_pics')
        
        db.session.commit()
        flash('Ваш профиль успешно обновлен!', 'success')
        return redirect(url_for('profile.view_profile', user_id=current_user.id))
    
    # Заполняем форму текущими данными
    elif request.method == 'GET':
        form.username.data = current_user.username
    
    return render_template('profile/update_profile.html', 
                          title='Редактирование профиля',
                          form=form)

@profile.route('/profile/<int:user_id>', methods=['GET'])
def view_profile(user_id):
    # Получаем пользователя по ID
    user = User.query.get_or_404(user_id)
    
    # Получаем заявки пользователя на мероприятия (если текущий пользователь - админ или это собственный профиль)
    applications = []
    if current_user.is_authenticated and (current_user.id == user.id or current_user.is_admin()):
        applications = EventApplication.query.filter_by(user_id=user.id).all()
    
    # Получаем организованные мероприятия (если пользователь - организатор)
    organized_events = []
    if user.is_organizer():
        organized_events = Event.query.filter_by(organizer_id=user.id).all()
    
    # Получаем достижения пользователя
    achievements = UserEventAchievement.query.filter_by(user_id=user.id).order_by(UserEventAchievement.date_earned.desc()).limit(10).all()
    
    return render_template('profile/user_profile.html', 
                          title=f'Профиль пользователя {user.username}',
                          user=user,
                          applications=applications,
                          organized_events=organized_events,
                          achievements=achievements)

@profile.route('/profile/applications')
@login_required
def user_applications():
    # Получаем заявки пользователя на мероприятия
    applications = EventApplication.query.filter_by(user_id=current_user.id).all()
    events = {app.event_id: Event.query.get(app.event_id) for app in applications}
    
    return render_template('profile/user_applications.html',
                          title='Мои заявки',
                          applications=applications,
                          events=events)

@profile.route('/user/<int:user_id>/achievements')
def user_achievements(user_id):
    user = User.query.get_or_404(user_id)
    
    # Получаем все достижения пользователя - и как участника, и как организатора
    user_rank = db.session.query(
        func.rank().over(
            order_by=func.sum(EventApplication.points).desc()
        ).label('rank')
    ).filter(EventApplication.user_id == user.id).scalar() or 0
    
    total_users = db.session.query(func.count(distinct(EventApplication.user_id))).scalar() or 0
    
    return render_template(
        'profile/user_achievements.html', 
        user=user,
        user_rank=user_rank,
        total_users=total_users
    )

@profile.route('/profile/events')
@login_required
def organized_events():
    # Проверяем, что пользователь является организатором
    if not current_user.is_organizer():
        flash('У вас нет прав для просмотра этой страницы', 'danger')
        return redirect(url_for('profile.view_profile', user_id=current_user.id))
    
    # Получаем мероприятия, организованные пользователем
    events = Event.query.filter_by(organizer_id=current_user.id).all()
    
    return render_template('profile/organized_events.html',
                          title='Мои мероприятия',
                          events=events)

@profile.route('/admin/user/<int:user_id>', methods=['GET'])
@login_required
def admin_view_user(user_id):
    # Проверяем, что текущий пользователь является администратором
    if not current_user.is_admin():
        flash('У вас нет прав для просмотра этой страницы', 'danger')
        return redirect(url_for('main.index'))
    
    # Получаем пользователя по ID
    user = User.query.get_or_404(user_id)
    
    # Получаем заявки пользователя
    applications = EventApplication.query.filter_by(user_id=user.id).all()
    
    # Получаем организованные мероприятия (если пользователь - организатор)
    organized_events = []
    if user.is_organizer():
        organized_events = Event.query.filter_by(organizer_id=user.id).all()
    
    return render_template('profile/user_profile.html', 
                          title=f'Профиль пользователя {user.username}',
                          user=user,
                          applications=applications,
                          organized_events=organized_events) 