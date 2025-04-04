from flask import Blueprint, jsonify, request, redirect, url_for
from flask_login import current_user, login_required
from app import db
from app.models.notification import Notification
import traceback

notifications = Blueprint('notifications', __name__)

@notifications.route('/notifications/<int:notification_id>/read', methods=['POST'])
@login_required
def mark_notification_read(notification_id):
    """Пометить уведомление как прочитанное"""
    try:
        notification = Notification.query.get_or_404(notification_id)
        
        # Проверяем, что уведомление принадлежит текущему пользователю
        if notification.user_id != current_user.id:
            return jsonify({'success': False, 'message': 'Доступ запрещен'}), 403
        
        notification.is_read = True
        db.session.commit()
        
        # Если запрос был через AJAX, возвращаем JSON
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': True})
        
        # Иначе редиректим на страницу, с которой пришел запрос
        return redirect(request.referrer or url_for('main.index'))
    except Exception as e:
        db.session.rollback()
        print(f"Error marking notification as read: {str(e)}")
        print(traceback.format_exc())
        return jsonify({'success': False, 'message': str(e)}), 500

@notifications.route('/notifications/read-all', methods=['POST'])
@login_required
def mark_all_notifications_read():
    """Пометить все уведомления пользователя как прочитанные"""
    try:
        notifications = Notification.query.filter_by(user_id=current_user.id, is_read=False).all()
        
        for notification in notifications:
            notification.is_read = True
        
        db.session.commit()
        
        # Если запрос был через AJAX, возвращаем JSON
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': True})
        
        # Иначе редиректим на страницу, с которой пришел запрос
        return redirect(request.referrer or url_for('main.index'))
    except Exception as e:
        db.session.rollback()
        print(f"Error marking all notifications as read: {str(e)}")
        print(traceback.format_exc())
        return jsonify({'success': False, 'message': str(e)}), 500

@notifications.route('/notifications', methods=['GET'])
@login_required
def get_notifications():
    """API для получения уведомлений пользователя"""
    try:
        # Получаем последние 10 уведомлений для текущего пользователя
        notifications = Notification.query.filter_by(user_id=current_user.id)\
            .order_by(Notification.created_at.desc())\
            .limit(10)\
            .all()
        
        # Формируем список уведомлений
        notifications_data = []
        for notification in notifications:
            notifications_data.append({
                'id': notification.id,
                'content': notification.content,
                'is_read': notification.is_read,
                'type': notification.type,
                'created_at': notification.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                'related_id': notification.related_id
            })
        
        # Подсчитываем общее количество непрочитанных уведомлений
        unread_count = Notification.query.filter_by(user_id=current_user.id, is_read=False).count()
        
        return jsonify({
            'notifications': notifications_data,
            'unread_count': unread_count
        })
    except Exception as e:
        print(f"Error getting notifications: {str(e)}")
        print(traceback.format_exc())
        return jsonify({'success': False, 'message': str(e)}), 500

# Маршруты совместимости для обратной совместимости
@notifications.route('/notifications/mark_read/<int:notification_id>', methods=['POST'])
@login_required
def old_mark_notification_read(notification_id):
    """Устаревший маршрут для совместимости"""
    return mark_notification_read(notification_id)
    
@notifications.route('/notifications/mark_all_read', methods=['POST'])
@login_required
def old_mark_all_notifications_read():
    """Устаревший маршрут для совместимости"""
    return mark_all_notifications_read() 