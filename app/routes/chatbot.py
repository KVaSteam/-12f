import requests
import json
from flask import Blueprint, render_template, request, jsonify, redirect, url_for
from flask_login import login_required, current_user
from app.models.user import UserRole

chatbot = Blueprint('chatbot', __name__)

# URL вашего развернутого Cloudflare Worker'а
WORKER_URL = "https://spring-union-aae1.bydymainit.workers.dev/"

def ask_ai_assistant(user_question, events_context_str, worker_url=WORKER_URL):
    """
    Отправляет запрос к Cloudflare Worker'у с вопросом и контекстом событий.
    """
    payload = {
        "message": user_question,
        "events_context": events_context_str
    }
    headers = {
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(worker_url, headers=headers, json=payload, timeout=60)
        response.raise_for_status()
        
        response_data = response.json()
        ai_response = response_data.get("response", "Ключ 'response' не найден в ответе JSON.")
        return ai_response
        
    except requests.exceptions.Timeout:
        return "Ошибка: Превышено время ожидания ответа от сервера."
    except requests.exceptions.RequestException as e:
        error_details = ""
        if hasattr(e, 'response') and e.response is not None:
            error_details = f" Детали от сервера: {e.response.status_code} - {e.response.text[:500]}"
        return f"Ошибка сети или HTTP при запросе к воркеру.{error_details}"
    except Exception as e:
        return f"Произошла непредвиденная ошибка при выполнении запроса: {str(e)}"

@chatbot.route('/chatbot')
@login_required
def chatbot_page():
    """Отображает страницу чат-бота"""
    # Доступ только для администраторов и организаторов
    if current_user.role not in [UserRole.ADMIN.value, UserRole.ORGANIZER.value]:
        return redirect(url_for('main.index'))
    
    return render_template('chatbot/chat.html', title='Чат-ассистент')

@chatbot.route('/api/chatbot', methods=['POST'])
@login_required
def chatbot_api():
    """API-эндпоинт для обработки запросов к чат-боту"""
    # Доступ только для администраторов и организаторов
    if current_user.role not in [UserRole.ADMIN.value, UserRole.ORGANIZER.value]:
        return jsonify({'error': 'Доступ запрещен'}), 403
    
    data = request.json
    
    if not data or 'message' not in data:
        return jsonify({'error': 'Отсутствует поле "message"'}), 400
    
    # Получаем контекст мероприятий из базы данных
    from app.models.event import Event
    from app.models.user import User
    
    events = Event.query.all()
    events_context = ""
    
    for event in events:
        organizer = User.query.get(event.organizer_id)
        events_context += f"""
        {event.title}
        Дата: {event.start_datetime.strftime('%d.%m.%Y %H:%M')} - {event.end_datetime.strftime('%d.%m.%Y %H:%M')}
        Место: {event.location}
        Организатор: {organizer.username}
        Описание: {event.description[:200]}...
        Статус: {event.status}
        """
    
    # Если контекст пустой, добавляем базовую информацию
    if not events_context.strip():
        events_context = "В системе пока нет мероприятий."
    
    # Отправляем запрос к AI
    answer = ask_ai_assistant(data['message'], events_context)
    
    return jsonify({'response': answer}) 