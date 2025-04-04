from flask import Blueprint, render_template, redirect, url_for, flash, request, abort, current_app
from flask_login import current_user, login_required
from app import db
from app.models import User, Event, EventStatus, News, Achievement, UserRole, Tag, EventApplication, OrganizerAchievement, UserOrganizerAchievement, Notification, NotificationType
from app.utils.forms import NewsForm, AchievementForm, OrganizerAchievementForm
from app.utils.helpers import save_image, admin_required
from sqlalchemy import func
from datetime import datetime

admin = Blueprint('admin', __name__)

@admin.route('/admin')
@login_required
@admin_required
def admin_dashboard():
    # Статистика для дашборда
    event_count = Event.query.count()
    user_count = User.query.count()
    pending_events = Event.query.filter_by(status=EventStatus.PENDING.value).count()
    
    # Топ организаторов по количеству мероприятий
    top_organizers = db.session.query(
        User, func.count(Event.id).label('event_count')
    ).join(Event, User.id == Event.organizer_id
    ).group_by(User.id
    ).order_by(func.count(Event.id).desc()
    ).limit(5).all()
    
    # Топ популярных тегов
    popular_tags = db.session.query(
        Tag, func.count(Event.id).label('tag_count')
    ).join(
        Event.tags
    ).group_by(Tag.id
    ).order_by(func.count(Event.id).desc()
    ).limit(10).all()
    
    return render_template('admin/dashboard.html',
                          title='Панель администратора',
                          event_count=event_count,
                          user_count=user_count,
                          pending_events=pending_events,
                          top_organizers=top_organizers,
                          popular_tags=popular_tags)

@admin.route('/admin/events/pending')
@login_required
@admin_required
def pending_events():
    """Страница со списком ожидающих модерации мероприятий"""
    events = Event.query.filter_by(status=EventStatus.PENDING.value).all()
    return render_template('admin/pending_events.html',
                          title='Ожидающие модерации мероприятия',
                          events=events)

@admin.route('/admin/event/<int:event_id>/approve', methods=['POST'])
@login_required
@admin_required
def approve_event(event_id):
    """Одобрение мероприятия"""
    event = Event.query.get_or_404(event_id)
    
    if event.status != EventStatus.PENDING.value:
        flash('Это мероприятие не ожидает модерации', 'warning')
        return redirect(url_for('admin.pending_events'))
    
    event.status = EventStatus.APPROVED.value
    db.session.commit()
    
    # Создаем уведомление для организатора
    notification = Notification(
        user_id=event.organizer_id,
        content=f'Ваше мероприятие "{event.title}" было одобрено администратором',
        type=NotificationType.EVENT_APPROVED.value,
        related_id=event.id
    )
    db.session.add(notification)
    db.session.commit()
    
    flash(f'Мероприятие "{event.title}" одобрено', 'success')
    return redirect(url_for('admin.pending_events'))

@admin.route('/admin/event/<int:event_id>/reject', methods=['POST'])
@login_required
@admin_required
def reject_event(event_id):
    """Отклонение мероприятия"""
    event = Event.query.get_or_404(event_id)
    
    if event.status != EventStatus.PENDING.value:
        flash('Это мероприятие не ожидает модерации', 'warning')
        return redirect(url_for('admin.pending_events'))
    
    event.status = EventStatus.REJECTED.value
    db.session.commit()
    
    # Создаем уведомление для организатора
    notification = Notification(
        user_id=event.organizer_id,
        content=f'Ваше мероприятие "{event.title}" было отклонено администратором',
        type=NotificationType.EVENT_REJECTED.value,
        related_id=event.id
    )
    db.session.add(notification)
    db.session.commit()
    
    flash(f'Мероприятие "{event.title}" отклонено', 'info')
    return redirect(url_for('admin.pending_events'))

@admin.route('/admin/news', methods=['GET'])
@login_required
@admin_required
def manage_news():
    news = News.query.order_by(News.published_at.desc()).all()
    return render_template('admin/manage_news.html',
                          title='Управление новостями',
                          news=news)

@admin.route('/admin/news/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create_news():
    form = NewsForm()
    
    if form.validate_on_submit():
        # Сохраняем изображение, если оно было загружено
        image_filename = 'default_news.jpg'
        if form.image.data:
            image_filename = save_image(form.image.data, 'news_images')
        
        # Создаем новость
        news = News(
            title=form.title.data,
            content=form.content.data,
            image=image_filename,
            author_id=current_user.id
        )
        
        db.session.add(news)
        db.session.commit()
        
        flash('Новость успешно создана', 'success')
        return redirect(url_for('admin.manage_news'))
    
    return render_template('admin/create_news.html',
                          title='Создание новости',
                          form=form,
                          legend='Создание новости')

@admin.route('/admin/news/<int:news_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_news(news_id):
    news = News.query.get_or_404(news_id)
    form = NewsForm()
    
    if form.validate_on_submit():
        # Обновляем данные новости
        news.title = form.title.data
        news.content = form.content.data
        
        # Обновляем изображение, если загружено новое
        if form.image.data:
            news.image = save_image(form.image.data, 'news_images')
        
        db.session.commit()
        flash('Новость успешно обновлена', 'success')
        return redirect(url_for('admin.manage_news'))
    
    # Заполняем форму текущими данными
    elif request.method == 'GET':
        form.title.data = news.title
        form.content.data = news.content
    
    return render_template('admin/create_news.html',
                          title='Редактирование новости',
                          form=form,
                          legend='Редактирование новости')

@admin.route('/admin/news/<int:news_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_news(news_id):
    news = News.query.get_or_404(news_id)
    db.session.delete(news)
    db.session.commit()
    flash('Новость удалена', 'success')
    return redirect(url_for('admin.manage_news'))

@admin.route('/admin/achievements', methods=['GET'])
@login_required
@admin_required
def manage_achievements():
    achievements = Achievement.query.all()
    return render_template('admin/manage_achievements.html',
                          title='Управление достижениями',
                          achievements=achievements)

@admin.route('/admin/achievements/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create_achievement():
    form = AchievementForm()
    
    if form.validate_on_submit():
        # Сохраняем иконку, если она была загружена
        icon_filename = 'default_achievement.png'
        if form.icon.data:
            icon_filename = save_image(form.icon.data, 'achievement_icons')
        
        # Создаем достижение
        achievement = Achievement(
            name=form.name.data,
            description=form.description.data,
            condition=form.condition.data,
            points=form.points.data,
            icon=icon_filename
        )
        
        db.session.add(achievement)
        db.session.commit()
        
        flash('Достижение успешно создано', 'success')
        return redirect(url_for('admin.manage_achievements'))
    
    return render_template('admin/create_achievement.html',
                          title='Создание достижения',
                          form=form,
                          legend='Создание достижения')

@admin.route('/admin/achievements/<int:achievement_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_achievement(achievement_id):
    achievement = Achievement.query.get_or_404(achievement_id)
    form = AchievementForm()
    
    if form.validate_on_submit():
        # Обновляем данные достижения
        achievement.name = form.name.data
        achievement.description = form.description.data
        achievement.condition = form.condition.data
        achievement.points = form.points.data
        
        # Обновляем иконку, если загружена новая
        if form.icon.data:
            achievement.icon = save_image(form.icon.data, 'achievement_icons')
        
        db.session.commit()
        flash('Достижение успешно обновлено', 'success')
        return redirect(url_for('admin.manage_achievements'))
    
    # Заполняем форму текущими данными
    elif request.method == 'GET':
        form.name.data = achievement.name
        form.description.data = achievement.description
        form.condition.data = achievement.condition
        form.points.data = achievement.points
    
    return render_template('admin/create_achievement.html',
                          title='Редактирование достижения',
                          form=form,
                          legend='Редактирование достижения')

@admin.route('/admin/achievements/<int:achievement_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_achievement(achievement_id):
    achievement = Achievement.query.get_or_404(achievement_id)
    db.session.delete(achievement)
    db.session.commit()
    flash('Достижение удалено', 'success')
    return redirect(url_for('admin.manage_achievements'))

@admin.route('/admin/users')
@login_required
@admin_required
def manage_users():
    users = User.query.all()
    return render_template('admin/manage_users.html',
                          title='Управление пользователями',
                          users=users)

@admin.route('/admin/user/<int:user_id>/toggle-role', methods=['POST'])
@login_required
@admin_required
def toggle_user_role(user_id):
    user = User.query.get_or_404(user_id)
    
    # Не позволяем изменять роль самому себе (администратору)
    if user.id == current_user.id:
        flash('Вы не можете изменить свою роль', 'danger')
        return redirect(url_for('admin.manage_users'))
    
    # Переключаем роль между участником и организатором
    if user.role == UserRole.PARTICIPANT.value:
        user.role = UserRole.ORGANIZER.value
        flash(f'Пользователь {user.username} теперь организатор', 'success')
    elif user.role == UserRole.ORGANIZER.value:
        user.role = UserRole.PARTICIPANT.value
        flash(f'Пользователь {user.username} теперь участник', 'success')
    
    db.session.commit()
    return redirect(url_for('admin.manage_users'))

@admin.route('/admin/statistics')
@login_required
@admin_required
def statistics():
    # Количество мероприятий по статусам
    event_stats = {
        'pending': Event.query.filter_by(status=EventStatus.PENDING.value).count(),
        'approved': Event.query.filter_by(status=EventStatus.APPROVED.value).count(),
        'rejected': Event.query.filter_by(status=EventStatus.REJECTED.value).count(),
        'total': Event.query.count()
    }
    
    # Количество пользователей по ролям
    user_stats = {
        'participants': User.query.filter_by(role=UserRole.PARTICIPANT.value).count(),
        'organizers': User.query.filter_by(role=UserRole.ORGANIZER.value).count(),
        'admins': User.query.filter_by(role=UserRole.ADMIN.value).count(),
        'total': User.query.count()
    }
    
    # Распределение заявок по статусам
    application_stats = {
        'pending': EventApplication.query.filter_by(status='pending').count(),
        'approved': EventApplication.query.filter_by(status='approved').count(),
        'rejected': EventApplication.query.filter_by(status='rejected').count(),
        'total': EventApplication.query.count()
    }
    
    return render_template('admin/statistics.html',
                          title='Статистика платформы',
                          event_stats=event_stats,
                          user_stats=user_stats,
                          application_stats=application_stats)

@admin.route('/admin/organizer-achievements')
@login_required
@admin_required
def organizer_achievements():
    """Страница со списком достижений для организаторов"""
    achievements = OrganizerAchievement.query.all()
    
    # Для каждого достижения подсчитываем, сколько организаторов его получили
    achievement_stats = {}
    for achievement in achievements:
        achievement_stats[achievement.id] = db.session.query(func.count(UserOrganizerAchievement.id)).\
            filter(UserOrganizerAchievement.achievement_id == achievement.id).scalar() or 0
    
    return render_template('admin/organizer_achievements.html',
                          title='Достижения организаторов',
                          achievements=achievements,
                          achievement_stats=achievement_stats)

@admin.route('/admin/organizer-achievement/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create_organizer_achievement():
    """Создание нового достижения для организаторов"""
    form = OrganizerAchievementForm()
    
    if form.validate_on_submit():
        # Сохраняем иконку, если она была загружена
        icon_filename = 'default_achievement.png'
        if form.icon.data:
            icon_filename = save_image(form.icon.data, 'achievement_icons')
        
        # Создаем новое достижение
        achievement = OrganizerAchievement(
            name=form.name.data,
            description=form.description.data,
            condition_type=form.condition_type.data,
            condition_value=form.condition_value.data,
            points=form.points.data,
            icon=icon_filename
        )
        
        db.session.add(achievement)
        db.session.commit()
        
        flash(f'Достижение "{form.name.data}" успешно создано', 'success')
        return redirect(url_for('admin.organizer_achievements'))
    
    return render_template('admin/create_organizer_achievement.html',
                          title='Создание достижения для организаторов',
                          form=form)

@admin.route('/admin/organizer-achievement/<int:achievement_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_organizer_achievement(achievement_id):
    """Редактирование достижения для организаторов"""
    achievement = OrganizerAchievement.query.get_or_404(achievement_id)
    form = OrganizerAchievementForm()
    
    if form.validate_on_submit():
        # Обновляем данные достижения
        achievement.name = form.name.data
        achievement.description = form.description.data
        achievement.condition_type = form.condition_type.data
        achievement.condition_value = form.condition_value.data
        achievement.points = form.points.data
        
        # Обновляем иконку, если загружена новая
        if form.icon.data:
            achievement.icon = save_image(form.icon.data, 'achievement_icons')
        
        db.session.commit()
        flash(f'Достижение "{achievement.name}" успешно обновлено', 'success')
        return redirect(url_for('admin.organizer_achievements'))
    
    # Заполняем форму текущими данными
    elif request.method == 'GET':
        form.name.data = achievement.name
        form.description.data = achievement.description
        form.condition_type.data = achievement.condition_type
        form.condition_value.data = achievement.condition_value
        form.points.data = achievement.points
    
    return render_template('admin/create_organizer_achievement.html',
                          title='Редактирование достижения для организаторов',
                          form=form,
                          achievement=achievement)

@admin.route('/admin/organizer-achievement/<int:achievement_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_organizer_achievement(achievement_id):
    """Удаление достижения для организаторов"""
    achievement = OrganizerAchievement.query.get_or_404(achievement_id)
    
    try:
        # Удаляем связанные записи UserOrganizerAchievement
        UserOrganizerAchievement.query.filter_by(achievement_id=achievement.id).delete()
        
        # Запомним имя для вывода в сообщении об успехе
        achievement_name = achievement.name
        
        # Удаляем достижение
        db.session.delete(achievement)
        db.session.commit()
        
        flash(f'Достижение "{achievement_name}" успешно удалено', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Не удалось удалить достижение: {str(e)}', 'danger')
    
    return redirect(url_for('admin.organizer_achievements')) 