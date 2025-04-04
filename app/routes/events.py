from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, abort, jsonify
from flask_login import current_user, login_required
from app import db
from app.models import Event, EventStatus, EventApplication, Tag, User, UserRole, EventAchievement, UserEventAchievement, EventReview, Notification, NotificationType
from app.utils.forms import EventForm, ApplicationActionForm, EventAchievementForm, EventReviewForm, EventApplicationForm
from app.utils.helpers import save_image, admin_required, generate_qr_code
from datetime import datetime
import os

events = Blueprint('events', __name__)

@events.route('/event/<int:event_id>')
def event_detail(event_id):
    event = Event.query.get_or_404(event_id)
    reviews = event.reviews.all()
    user_application = None
    
    # Check if user has already applied for this event
    if current_user.is_authenticated:
        user_application = EventApplication.query.filter_by(
            event_id=event_id, 
            user_id=current_user.id
        ).first()
        
    # Process event description to replace bullet points with proper HTML
    formatted_description = event.description
    
    # Генерируем QR-код для ссылки на мероприятие
    event_url = request.url_root[:-1] + url_for('events.event_detail', event_id=event.id)
    qr_code = generate_qr_code(event_url)
    
    return render_template(
        'events/event_detail.html', 
        event=event, 
        reviews=reviews, 
        user_application=user_application,
        qr_code=qr_code
    )

@events.route('/event/create', methods=['GET', 'POST'])
@login_required
def create_event():
    # Проверяем, что пользователь является организатором или администратором
    if not current_user.is_organizer():
        flash('У вас нет прав для создания мероприятий', 'danger')
        return redirect(url_for('main.index'))
    
    form = EventForm()
    
    # Получаем список тегов для выбора
    form.tags.choices = [(tag.id, tag.name) for tag in Tag.query.all()]
    
    if form.validate_on_submit():
        # Сохраняем логотип, если он был загружен
        logo_filename = 'default_event.jpg'
        if form.logo.data:
            logo_filename = save_image(form.logo.data, 'event_logos')
        
        # Создаем новое событие
        event = Event(
            title=form.title.data,
            description=form.description.data,
            start_datetime=form.start_datetime.data,
            end_datetime=form.end_datetime.data,
            location=form.location.data,
            format=form.format.data,
            logo=logo_filename,
            organizer_id=current_user.id,
            status=EventStatus.PENDING.value,  # Новое событие отправляется на модерацию
            default_points=form.default_points.data,  # Добавляем очки по умолчанию
            max_participants=form.max_participants.data  # Добавляем максимальное количество участников
        )
        
        # Добавляем выбранные теги
        for tag_id in form.tags.data:
            tag = Tag.query.get(tag_id)
            if tag:
                event.tags.append(tag)
        
        db.session.add(event)
        db.session.commit()
        
        flash('Ваше мероприятие создано и отправлено на модерацию', 'success')
        return redirect(url_for('events.event_detail', event_id=event.id))
    
    return render_template('events/create_event.html', 
                          title='Создание мероприятия', 
                          form=form, 
                          legend='Создание нового мероприятия')

@events.route('/event/<int:event_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_event(event_id):
    event = Event.query.get_or_404(event_id)
    
    # Проверяем права на редактирование события
    if event.organizer_id != current_user.id and not current_user.is_admin():
        abort(403)
    
    # Если событие уже одобрено, обычный организатор не может его редактировать
    if event.status == EventStatus.APPROVED.value and event.organizer_id == current_user.id and not current_user.is_admin():
        flash('Одобренное мероприятие может редактировать только администратор', 'warning')
        return redirect(url_for('events.event_detail', event_id=event.id))
    
    form = EventForm()
    form.tags.choices = [(tag.id, tag.name) for tag in Tag.query.all()]
    
    if form.validate_on_submit():
        # Обновляем данные события
        event.title = form.title.data
        event.description = form.description.data
        event.start_datetime = form.start_datetime.data
        event.end_datetime = form.end_datetime.data
        event.location = form.location.data
        event.format = form.format.data
        event.max_participants = form.max_participants.data
        
        # Обновляем логотип, если загружен новый
        if form.logo.data:
            event.logo = save_image(form.logo.data, 'event_logos')
        
        # Обновляем теги
        event.tags = []
        for tag_id in form.tags.data:
            tag = Tag.query.get(tag_id)
            if tag:
                event.tags.append(tag)
        
        # Если организатор редактирует событие, оно возвращается на модерацию
        if not current_user.is_admin():
            event.status = EventStatus.PENDING.value
            flash('Ваше мероприятие обновлено и отправлено на повторную модерацию', 'info')
        else:
            flash('Мероприятие успешно обновлено', 'success')
        
        db.session.commit()
        return redirect(url_for('events.event_detail', event_id=event.id))
    
    # Заполняем форму текущими данными события
    elif request.method == 'GET':
        form.title.data = event.title
        form.description.data = event.description
        form.start_datetime.data = event.start_datetime
        form.end_datetime.data = event.end_datetime
        form.location.data = event.location
        form.format.data = event.format
        form.max_participants.data = event.max_participants
        form.tags.data = [tag.id for tag in event.tags]
    
    return render_template('events/create_event.html', 
                          title='Редактирование мероприятия', 
                          form=form, 
                          legend='Редактирование мероприятия')

@events.route('/event/<int:event_id>/apply', methods=['GET', 'POST'])
@login_required
def apply_for_event(event_id):
    event = Event.query.get_or_404(event_id)
    
    # Проверяем, что пользователь не является организатором мероприятия
    if event.organizer_id == current_user.id:
        flash('Вы не можете подать заявку на собственное мероприятие', 'warning')
        return redirect(url_for('events.event_detail', event_id=event.id))
    
    # Проверяем, что мероприятие активно
    if event.status != EventStatus.APPROVED.value:
        flash('Вы не можете подать заявку на неактивное мероприятие', 'warning')
        return redirect(url_for('events.event_detail', event_id=event.id))
    
    # Проверяем, что не превышено максимальное количество участников
    if event.max_participants and event.max_participants > 0:
        approved_count = EventApplication.query.filter_by(
            event_id=event.id,
            status='approved'
        ).count()
        
        if approved_count >= event.max_participants:
            flash('К сожалению, все места на мероприятие заняты', 'warning')
            return redirect(url_for('events.event_detail', event_id=event.id))
    
    # Проверяем, что пользователь еще не подал заявку
    existing_application = EventApplication.query.filter_by(
        user_id=current_user.id,
        event_id=event.id
    ).first()
    
    if existing_application:
        flash('Вы уже подали заявку на это мероприятие', 'info')
        return redirect(url_for('events.event_detail', event_id=event.id))
    
    form = EventApplicationForm()
    
    if form.validate_on_submit():
        # Создаем новую заявку
        application = EventApplication(
            user_id=current_user.id,
            event_id=event.id,
            status='pending'
        )
        
        db.session.add(application)
        db.session.commit()
        
        # Создаем уведомление для организатора
        notification = Notification(
            user_id=event.organizer_id,
            content=f'Новая заявка на участие в мероприятии "{event.title}"',
            type=NotificationType.EVENT_APPLICATION.value,
            related_id=event.id
        )
        db.session.add(notification)
        db.session.commit()
        
        flash('Ваша заявка успешно отправлена', 'success')
        return redirect(url_for('events.event_detail', event_id=event.id))
    
    return render_template('events/apply_for_event.html',
                          title='Подача заявки',
                          event=event,
                          form=form)

@events.route('/event/<int:event_id>/cancel-application', methods=['POST'])
@login_required
def cancel_application(event_id):
    application = EventApplication.query.filter_by(
        user_id=current_user.id, 
        event_id=event_id
    ).first_or_404()
    
    # Проверяем статус заявки (можно отменить только в статусе pending)
    if application.status == 'pending':
        db.session.delete(application)
        db.session.commit()
        flash('Заявка отменена', 'info')
    else:
        flash('Невозможно отменить эту заявку', 'danger')
    
    return redirect(url_for('events.event_detail', event_id=event_id))

@events.route('/event/<int:event_id>/applications', methods=['GET', 'POST'])
@login_required
def manage_applications(event_id):
    event = Event.query.get_or_404(event_id)
    
    # Проверяем права на управление заявками
    if event.organizer_id != current_user.id and not current_user.is_admin():
        flash('У вас нет прав для управления заявками на это мероприятие', 'danger')
        return redirect(url_for('events.event_detail', event_id=event.id))
    
    # Получаем параметры для фильтрации
    status_filter = request.args.get('status', 'all')
    
    # Базовый запрос
    applications_query = EventApplication.query.filter_by(event_id=event.id)
    
    # Применяем фильтр по статусу
    if status_filter != 'all':
        applications_query = applications_query.filter_by(status=status_filter)
    
    # Получаем заявки
    applications = applications_query.all()
    
    # Создаем словарь с пользователями для быстрого доступа
    user_ids = [app.user_id for app in applications]
    users_query = User.query.filter(User.id.in_(user_ids)).all()
    users = {user.id: user for user in users_query}
    
    # Создаем форму для обработки действий с заявками
    form = ApplicationActionForm()
    
    # Обработка формы
    if request.method == 'POST':
        application_id = request.form.get('application_id')
        action = request.form.get('action')
        
        if application_id and action:
            application = EventApplication.query.get_or_404(application_id)
            
            # Проверяем, что заявка относится к этому мероприятию
            if application.event_id != event.id:
                flash('Неверный идентификатор заявки', 'danger')
                return redirect(url_for('events.manage_applications', event_id=event.id))
            
            if action == 'approve':
                # Проверяем, что не превышено максимальное количество участников
                if event.max_participants and event.max_participants > 0:
                    approved_count = EventApplication.query.filter_by(
                        event_id=event.id,
                        status='approved'
                    ).count()
                    
                    if approved_count >= event.max_participants:
                        flash('Максимальное количество участников уже достигнуто', 'warning')
                        return redirect(url_for('events.manage_applications', event_id=event.id))
                
                application.status = 'approved'
                flash('Заявка одобрена', 'success')
                
                # Создаем уведомление для пользователя
                notification = Notification(
                    user_id=application.user_id,
                    content=f'Ваша заявка на участие в мероприятии "{event.title}" была одобрена',
                    type=NotificationType.APPLICATION_APPROVED.value,
                    related_id=event.id
                )
                db.session.add(notification)
                
            elif action == 'reject':
                application.status = 'rejected'
                flash('Заявка отклонена', 'info')
                
                # Создаем уведомление для пользователя
                notification = Notification(
                    user_id=application.user_id,
                    content=f'Ваша заявка на участие в мероприятии "{event.title}" была отклонена',
                    type=NotificationType.APPLICATION_REJECTED.value,
                    related_id=event.id
                )
                db.session.add(notification)
                
            db.session.commit()
    
    return render_template('events/manage_applications.html',
                          title='Управление заявками',
                          event=event,
                          applications=applications,
                          users=users,
                          status_filter=status_filter,
                          form=form)

@events.route('/event/<int:event_id>/application/<int:app_id>/action', methods=['POST'])
@login_required
def application_action(event_id, app_id):
    """Обработка действий с заявками (одобрение/отклонение)"""
    event = Event.query.get_or_404(event_id)
    application = EventApplication.query.get_or_404(app_id)
    
    # Проверяем права на управление заявками
    if event.organizer_id != current_user.id and not current_user.is_admin():
        flash('У вас нет прав для управления заявками на это мероприятие', 'danger')
        return redirect(url_for('events.event_detail', event_id=event.id))
    
    # Проверяем, что заявка относится к этому мероприятию
    if application.event_id != event.id:
        flash('Неверный идентификатор заявки', 'danger')
        return redirect(url_for('events.manage_applications', event_id=event.id))
    
    action = request.form.get('action')
    
    if action == 'approve':
        # Проверяем, что не превышено максимальное количество участников
        if event.max_participants and event.max_participants > 0:
            approved_count = EventApplication.query.filter_by(
                event_id=event.id,
                status='approved'
            ).count()
            
            if approved_count >= event.max_participants and application.status != 'approved':
                flash('Максимальное количество участников уже достигнуто', 'warning')
                return redirect(url_for('events.manage_applications', event_id=event.id))
        
        application.status = 'approved'
        flash('Заявка одобрена', 'success')
        
        # Создаем уведомление для пользователя
        notification = Notification(
            user_id=application.user_id,
            content=f'Ваша заявка на участие в мероприятии "{event.title}" была одобрена',
            type=NotificationType.APPLICATION_APPROVED.value,
            related_id=event.id
        )
        db.session.add(notification)
        
    elif action == 'reject':
        application.status = 'rejected'
        flash('Заявка отклонена', 'info')
        
        # Создаем уведомление для пользователя
        notification = Notification(
            user_id=application.user_id,
            content=f'Ваша заявка на участие в мероприятии "{event.title}" была отклонена',
            type=NotificationType.APPLICATION_REJECTED.value,
            related_id=event.id
        )
        db.session.add(notification)
    
    db.session.commit()
    return redirect(url_for('events.manage_applications', event_id=event.id))

@events.route('/events/create_tag', methods=['POST'])
@login_required
@admin_required
def create_tag():
    """Создание нового тега (только для администраторов)"""
    # Проверяем, что данные в формате JSON
    if not request.is_json:
        return jsonify({'success': False, 'error': 'Необходим JSON формат'}), 400
        
    data = request.get_json()
    
    if not data or 'name' not in data:
        return jsonify({'success': False, 'error': 'Не указано название тега'}), 400
    
    tag_name = data['name'].strip()
    
    if not tag_name:
        return jsonify({'success': False, 'error': 'Название тега не может быть пустым'}), 400
    
    # Проверяем, существует ли тег с таким именем
    existing_tag = Tag.query.filter(Tag.name.ilike(tag_name)).first()
    if existing_tag:
        return jsonify({'success': False, 'error': 'Тег с таким названием уже существует'}), 400
    
    # Создаем новый тег
    try:
        new_tag = Tag(name=tag_name)
        db.session.add(new_tag)
        db.session.commit()
        
        # Возвращаем данные нового тега
        return jsonify({
            'success': True,
            'id': new_tag.id,
            'name': new_tag.name
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': f'Ошибка при создании тега: {str(e)}'}), 500

@events.route('/events/delete_tag/<int:tag_id>', methods=['POST'])
@login_required
@admin_required
def delete_tag(tag_id):
    """Удаление тега (только для администраторов)"""
    tag = Tag.query.get_or_404(tag_id)
    
    try:
        # Запомним имя для вывода в сообщении об успехе
        tag_name = tag.name
        
        # Удаляем тег
        db.session.delete(tag)
        db.session.commit()
        
        flash(f'Тег "{tag_name}" успешно удален', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Не удалось удалить тег: {str(e)}', 'danger')
    
    return redirect(url_for('events.manage_tags'))

@events.route('/events/manage_tags', methods=['GET'])
@login_required
@admin_required
def manage_tags():
    """Страница управления тегами (только для администраторов)"""
    tags = Tag.query.order_by(Tag.name).all()
    
    # Для каждого тега подсчитаем, сколько мероприятий его используют
    tag_stats = {}
    for tag in tags:
        tag_stats[tag.id] = len(tag.events.all())
    
    return render_template('events/manage_tags.html',
                          title='Управление тегами',
                          tags=tags,
                          tag_stats=tag_stats)

@events.route('/event/<int:event_id>/complete', methods=['GET', 'POST'])
@login_required
def complete_event(event_id):
    event = Event.query.get_or_404(event_id)
    
    # Проверяем права на завершение мероприятия
    if event.organizer_id != current_user.id and not current_user.is_admin():
        flash('У вас нет прав для завершения этого мероприятия', 'danger')
        return redirect(url_for('events.event_detail', event_id=event.id))
    
    # Проверяем, что мероприятие можно завершить
    if event.status != EventStatus.APPROVED.value:
        flash('Только одобренные мероприятия могут быть завершены', 'warning')
        return redirect(url_for('events.event_detail', event_id=event.id))
    
    # Получаем все одобренные заявки на это мероприятие
    approved_applications = EventApplication.query.filter_by(
        event_id=event.id,
        status='approved'
    ).all()
    
    # Получаем все достижения мероприятия
    achievements = EventAchievement.query.filter_by(event_id=event.id).all()
    
    if request.method == 'POST':
        # Обновляем статус мероприятия
        event.status = EventStatus.COMPLETED.value
        
        # Присваиваем очки участникам и выдаем достижения
        for application in approved_applications:
            # Обработка очков за участие
            points_key = f'points_{application.id}'
            if points_key in request.form:
                try:
                    points = int(request.form[points_key])
                    if 0 <= points <= 100:  # Проверяем, что очки в допустимом диапазоне
                        application.points = points
                except ValueError:
                    pass  # Игнорируем некорректные значения
            
            # Обработка достижений
            for achievement in achievements:
                achievement_key = f'achievement_{application.id}_{achievement.id}'
                if achievement_key in request.form:
                    # Проверяем, не было ли уже присвоено это достижение
                    existing_achievement = UserEventAchievement.query.filter_by(
                        user_id=application.user_id,
                        achievement_id=achievement.id
                    ).first()
                    
                    if not existing_achievement:
                        # Создаем новое достижение пользователя
                        user_achievement = UserEventAchievement(
                            user_id=application.user_id,
                            achievement_id=achievement.id,
                            event_id=event.id,
                            date_earned=datetime.now()
                        )
                        db.session.add(user_achievement)
                        
                        # Создаем уведомление о получении достижения
                        notification = Notification(
                            user_id=application.user_id,
                            content=f'Вы получили достижение "{achievement.name}" за участие в мероприятии "{event.title}"',
                            type=NotificationType.ACHIEVEMENT_EARNED.value,
                            related_id=achievement.id
                        )
                        db.session.add(notification)
            
            # Создаем уведомление о завершении мероприятия
            notification = Notification(
                user_id=application.user_id,
                content=f'Мероприятие "{event.title}" было завершено. Вы получили {application.points} очков.',
                type=NotificationType.EVENT_COMPLETED.value,
                related_id=event.id
            )
            db.session.add(notification)
        
        db.session.commit()
        
        # Проверяем условия для получения достижений организатором
        check_organizer_achievements(event.organizer_id, event)
        
        flash('Мероприятие завершено, очки и достижения распределены', 'success')
        return redirect(url_for('events.event_detail', event_id=event.id))
    
    # Форма для GET запроса
    form = ApplicationActionForm()
    
    return render_template('events/complete_event.html',
                          title='Завершение мероприятия',
                          event=event,
                          approved_applications=approved_applications,
                          achievements=achievements,
                          form=form)

def check_organizer_achievements(organizer_id, event):
    """Проверяет выполнение условий для получения достижений организатором"""
    from app.models.achievement import OrganizerAchievement, AchievementConditionType
    from app.models.user import UserOrganizerAchievement, User
    
    organizer = User.query.get_or_404(organizer_id)
    
    # Получаем все организаторские достижения
    achievements = OrganizerAchievement.query.all()
    
    # Проверяем каждое достижение
    for achievement in achievements:
        # Проверяем, не получено ли уже это достижение
        existing = UserOrganizerAchievement.query.filter_by(
            user_id=organizer_id,
            achievement_id=achievement.id
        ).first()
        
        if existing:
            continue  # Пропускаем, если уже есть
        
        # Проверяем условия в зависимости от типа достижения
        if achievement.condition_type == AchievementConditionType.PARTICIPANTS_COUNT.value:
            # Проверяем количество участников в текущем мероприятии
            participants_count = event.participants_count()
            
            if participants_count >= achievement.condition_value:
                # Выдаем достижение
                user_achievement = UserOrganizerAchievement(
                    user_id=organizer_id,
                    achievement_id=achievement.id,
                    date_earned=datetime.now()
                )
                db.session.add(user_achievement)
                
        elif achievement.condition_type == AchievementConditionType.EVENTS_COUNT.value:
            # Проверяем общее количество проведенных мероприятий
            events_count = organizer.count_completed_events()
            
            if events_count >= achievement.condition_value:
                # Выдаем достижение
                user_achievement = UserOrganizerAchievement(
                    user_id=organizer_id,
                    achievement_id=achievement.id,
                    date_earned=datetime.now()
                )
                db.session.add(user_achievement)
    
    # Сохраняем изменения
    db.session.commit()

@events.route('/event/<int:event_id>/achievements', methods=['GET'])
@login_required
def manage_achievements(event_id):
    event = Event.query.get_or_404(event_id)
    
    # Проверяем права на управление достижениями
    if event.organizer_id != current_user.id and not current_user.is_admin():
        flash('У вас нет прав для управления достижениями этого мероприятия', 'danger')
        return redirect(url_for('events.event_detail', event_id=event.id))
    
    # Получаем все достижения мероприятия
    achievements = EventAchievement.query.filter_by(event_id=event.id).all()
    
    return render_template('events/manage_achievements.html',
                          title='Управление достижениями',
                          event=event,
                          achievements=achievements)

@events.route('/event/<int:event_id>/achievement/create', methods=['GET', 'POST'])
@login_required
def create_achievement(event_id):
    event = Event.query.get_or_404(event_id)
    
    # Проверяем права на создание достижений
    if event.organizer_id != current_user.id and not current_user.is_admin():
        flash('У вас нет прав для создания достижений этого мероприятия', 'danger')
        return redirect(url_for('events.event_detail', event_id=event.id))
    
    form = EventAchievementForm()
    
    if form.validate_on_submit():
        # Сохраняем иконку, если она была загружена
        icon_filename = 'default_achievement.png'
        if form.icon.data:
            icon_filename = save_image(form.icon.data, 'achievement_icons')
        
        # Создаем новое достижение
        achievement = EventAchievement(
            name=form.name.data,
            description=form.description.data,
            points=form.points.data,
            icon=icon_filename,
            event_id=event.id
        )
        
        db.session.add(achievement)
        db.session.commit()
        
        flash('Достижение успешно создано', 'success')
        return redirect(url_for('events.manage_achievements', event_id=event.id))
    
    return render_template('events/create_achievement.html',
                          title='Создание достижения',
                          form=form,
                          event=event)

@events.route('/event/<int:event_id>/achievement/<int:achievement_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_achievement(event_id, achievement_id):
    event = Event.query.get_or_404(event_id)
    achievement = EventAchievement.query.get_or_404(achievement_id)
    
    # Проверяем, что достижение принадлежит мероприятию
    if achievement.event_id != event.id:
        abort(404)
    
    # Проверяем права на редактирование достижений
    if event.organizer_id != current_user.id and not current_user.is_admin():
        flash('У вас нет прав для редактирования достижений этого мероприятия', 'danger')
        return redirect(url_for('events.event_detail', event_id=event.id))
    
    form = EventAchievementForm()
    
    if form.validate_on_submit():
        # Обновляем данные достижения
        achievement.name = form.name.data
        achievement.description = form.description.data
        achievement.points = form.points.data
        
        # Обновляем иконку, если загружена новая
        if form.icon.data:
            achievement.icon = save_image(form.icon.data, 'achievement_icons')
        
        db.session.commit()
        flash('Достижение успешно обновлено', 'success')
        return redirect(url_for('events.manage_achievements', event_id=event.id))
    
    # Заполняем форму текущими данными
    elif request.method == 'GET':
        form.name.data = achievement.name
        form.description.data = achievement.description
        form.points.data = achievement.points
    
    return render_template('events/create_achievement.html',
                          title='Редактирование достижения',
                          form=form,
                          event=event,
                          achievement=achievement)

@events.route('/event/<int:event_id>/achievement/<int:achievement_id>/delete', methods=['POST'])
@login_required
def delete_achievement(event_id, achievement_id):
    event = Event.query.get_or_404(event_id)
    achievement = EventAchievement.query.get_or_404(achievement_id)
    
    # Проверяем, что достижение принадлежит мероприятию
    if achievement.event_id != event.id:
        abort(404)
    
    # Проверяем права на удаление достижений
    if event.organizer_id != current_user.id and not current_user.is_admin():
        flash('У вас нет прав для удаления достижений этого мероприятия', 'danger')
        return redirect(url_for('events.event_detail', event_id=event.id))
    
    # Удаляем связанные записи UserEventAchievement
    UserEventAchievement.query.filter_by(achievement_id=achievement.id).delete()
    
    # Удаляем достижение
    db.session.delete(achievement)
    db.session.commit()
    
    flash('Достижение успешно удалено', 'success')
    return redirect(url_for('events.manage_achievements', event_id=event.id))

@events.route('/event/<int:event_id>/delete', methods=['POST'])
@login_required
def delete_event(event_id):
    event = Event.query.get_or_404(event_id)
    
    # Проверяем права на удаление мероприятия
    if event.organizer_id != current_user.id and not current_user.is_admin():
        flash('У вас нет прав для удаления этого мероприятия', 'danger')
        return redirect(url_for('events.event_detail', event_id=event.id))
    
    # Удаляем связанные записи достижений
    EventAchievement.query.filter_by(event_id=event.id).delete()
    
    # Удаляем связанные заявки
    EventApplication.query.filter_by(event_id=event.id).delete()
    
    # Удаляем мероприятие
    db.session.delete(event)
    db.session.commit()
    
    flash(f'Мероприятие "{event.title}" успешно удалено', 'success')
    return redirect(url_for('main.index'))

@events.route('/event/<int:event_id>/review', methods=['POST'])
@login_required
def submit_review(event_id):
    event = Event.query.get_or_404(event_id)
    
    # Проверяем, завершено ли мероприятие
    if event.status != EventStatus.COMPLETED.value:
        flash('Отзывы можно оставлять только для завершенных мероприятий', 'warning')
        return redirect(url_for('events.event_detail', event_id=event.id))
    
    # Проверяем, был ли пользователь участником мероприятия
    user_application = EventApplication.query.filter_by(
        user_id=current_user.id,
        event_id=event.id,
        status='approved'
    ).first()
    
    if not user_application and not current_user.is_admin():
        flash('Только участники мероприятия могут оставлять отзывы', 'warning')
        return redirect(url_for('events.event_detail', event_id=event.id))
    
    # Проверяем, не оставил ли пользователь уже отзыв
    existing_review = EventReview.query.filter_by(
        user_id=current_user.id,
        event_id=event.id
    ).first()
    
    if existing_review:
        flash('Вы уже оставили отзыв об этом мероприятии', 'info')
        return redirect(url_for('events.event_detail', event_id=event.id))
    
    form = EventReviewForm()
    
    if form.validate_on_submit():
        review = EventReview(
            user_id=current_user.id,
            event_id=event.id,
            rating=form.rating.data,
            comment=form.comment.data,
            created_at=datetime.now()
        )
        
        db.session.add(review)
        db.session.commit()
        
        flash('Ваш отзыв успешно добавлен', 'success')
    else:
        flash('Ошибка при добавлении отзыва. Пожалуйста, проверьте введенные данные.', 'danger')
    
    return redirect(url_for('events.event_detail', event_id=event.id))

@events.route('/event/<int:event_id>/review/edit/<int:review_id>', methods=['GET', 'POST'])
@login_required
def edit_review(event_id, review_id):
    event = Event.query.get_or_404(event_id)
    review = EventReview.query.get_or_404(review_id)
    
    # Проверяем, что отзыв принадлежит текущему пользователю
    if review.user_id != current_user.id:
        flash('У вас нет прав для редактирования этого отзыва', 'danger')
        return redirect(url_for('events.event_detail', event_id=event.id))
    
    form = EventReviewForm()
    
    if form.validate_on_submit():
        # Обновляем данные отзыва
        review.rating = form.rating.data
        review.comment = form.comment.data
        
        db.session.commit()
        flash('Ваш отзыв успешно обновлен', 'success')
        return redirect(url_for('events.event_detail', event_id=event.id))
    
    # Заполняем форму текущими данными отзыва
    elif request.method == 'GET':
        form.rating.data = review.rating
        form.comment.data = review.comment
    
    return render_template('events/edit_review.html',
                          title='Редактирование отзыва',
                          form=form,
                          event=event,
                          review=review)

@events.route('/event/<int:event_id>/review/delete/<int:review_id>', methods=['POST'])
@login_required
def delete_review(event_id, review_id):
    event = Event.query.get_or_404(event_id)
    review = EventReview.query.get_or_404(review_id)
    
    # Проверяем, что пользователь имеет права на удаление отзыва (админ или автор отзыва)
    if not current_user.is_admin() and review.user_id != current_user.id:
        flash('У вас нет прав для удаления этого отзыва', 'danger')
        return redirect(url_for('events.event_detail', event_id=event.id))
    
    db.session.delete(review)
    db.session.commit()
    
    flash('Отзыв успешно удален', 'success')
    return redirect(url_for('events.event_detail', event_id=event.id)) 