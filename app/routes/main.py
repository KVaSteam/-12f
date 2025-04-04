from flask import Blueprint, render_template, request
from app.models import Event, News, EventStatus, Tag
from app.utils.forms import EventFilterForm
from datetime import datetime, timedelta, date
import calendar

main = Blueprint('main', __name__)

@main.route('/')
def index():
    # Получаем текущую дату для фильтрации событий
    now = datetime.utcnow()
    
    # Получаем одобренные предстоящие события для календаря
    upcoming_events = Event.query.filter(
        Event.status == EventStatus.APPROVED.value,
        Event.start_datetime > now
    ).order_by(Event.start_datetime).all()
    
    # Получаем последние новости
    latest_news = News.query.order_by(News.published_at.desc()).limit(5).all()
    
    return render_template('main/index.html', 
                          title='Главная',
                          upcoming_events=upcoming_events,
                          latest_news=latest_news,
                          current_date=now)

@main.route('/news')
def news_list():
    page = request.args.get('page', 1, type=int)
    sort_order = request.args.get('sort_order', 'desc')
    
    # Сортировка новостей по дате публикации
    if sort_order == 'asc':
        news = News.query.order_by(News.published_at.asc()).paginate(page=page, per_page=10)
    else:  # desc (по умолчанию)
        news = News.query.order_by(News.published_at.desc()).paginate(page=page, per_page=10)
    
    return render_template('main/news_list.html', title='Новости', news=news, current_sort=sort_order)

@main.route('/news/<int:news_id>')
def news_detail(news_id):
    news = News.query.get_or_404(news_id)
    return render_template('main/news_detail.html', title=news.title, news=news)

@main.route('/calendar')
def calendar_view():
    # Создаем форму фильтрации
    form = EventFilterForm()
    form.tags.choices = [(tag.id, tag.name) for tag in Tag.query.order_by(Tag.name).all()]
    
    # Получаем параметры фильтрации из запроса
    month = request.args.get('month', datetime.utcnow().month, type=int)
    year = request.args.get('year', datetime.utcnow().year, type=int)
    start_date_param = request.args.get('start_date')
    end_date_param = request.args.get('end_date')
    event_format = request.args.get('event_format', '')
    status = request.args.get('status', '')
    tags = request.args.getlist('tags', type=int)
    
    # Преобразуем параметры в объекты datetime, если они есть
    custom_start_date = None
    custom_end_date = None
    
    if start_date_param:
        try:
            custom_start_date = datetime.strptime(start_date_param, '%Y-%m-%dT%H:%M')
        except ValueError:
            pass
    
    if end_date_param:
        try:
            custom_end_date = datetime.strptime(end_date_param, '%Y-%m-%dT%H:%M')
        except ValueError:
            pass
    
    # Если указаны пользовательские даты, используем их для фильтрации
    if custom_start_date and custom_end_date:
        start_date = custom_start_date
        end_date = custom_end_date
    else:
        # Получаем первый и последний день месяца
        start_date = datetime(year, month, 1)
        if month == 12:
            end_date = datetime(year + 1, 1, 1) - timedelta(days=1)
            next_month, next_year = 1, year + 1
        else:
            end_date = datetime(year, month + 1, 1) - timedelta(days=1)
            next_month, next_year = month + 1, year
        
        # Устанавливаем конец дня для end_date
        end_date = end_date.replace(hour=23, minute=59, second=59)
    
    # Расчет предыдущего и следующего месяца для навигации
    if month == 1:
        prev_month, prev_year = 12, year - 1
    else:
        prev_month, prev_year = month - 1, year
    
    # Базовый запрос для мероприятий
    events_query = Event.query
    
    # Фильтр по датам
    if custom_start_date:
        events_query = events_query.filter(Event.start_datetime >= custom_start_date)
    else:
        events_query = events_query.filter(Event.start_datetime >= start_date)
    
    if custom_end_date:
        events_query = events_query.filter(Event.start_datetime <= custom_end_date)
    else:
        events_query = events_query.filter(Event.start_datetime <= end_date)
    
    # Фильтр по статусу (активные/завершенные)
    if status == 'active':
        events_query = events_query.filter(Event.status == EventStatus.APPROVED.value)
    elif status == 'completed':
        events_query = events_query.filter(Event.status == EventStatus.COMPLETED.value)
    else:
        # По умолчанию показываем все одобренные и завершенные мероприятия
        events_query = events_query.filter(Event.status.in_([EventStatus.APPROVED.value, EventStatus.COMPLETED.value]))
    
    # Фильтр по формату мероприятия
    if event_format:
        events_query = events_query.filter(Event.format == event_format)
    
    # Фильтр по тегам
    if tags:
        for tag_id in tags:
            events_query = events_query.filter(Event.tags.any(Tag.id == tag_id))
    
    # Получаем отфильтрованные мероприятия
    events = events_query.order_by(Event.start_datetime).all()
    
    # Подготовка календаря для отображения
    cal = calendar.monthcalendar(year, month)
    calendar_days = []
    day_events_map = {}  # Словарь для хранения событий по дням
    
    # Группировка событий по дням
    for event in events:
        event_date = event.start_datetime.date()
        key = (event_date.year, event_date.month, event_date.day)
        if key not in day_events_map:
            day_events_map[key] = []
        day_events_map[key].append(event)
    
    # Подготовка данных для шаблона
    for week in cal:
        week_days = []
        for day in week:
            if day == 0:
                week_days.append((day, None))  # Дни, не входящие в текущий месяц
            else:
                week_days.append((day, date(year, month, day)))
        calendar_days.append(week_days)
    
    # Названия месяцев и дней недели
    month_names = ['Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь', 
                  'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь']
    month_abbr = ['Янв', 'Фев', 'Мар', 'Апр', 'Май', 'Июн', 'Июл', 'Авг', 'Сен', 'Окт', 'Ноя', 'Дек']
    weekdays = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс']
    
    # Заполняем форму значениями из запроса
    if start_date_param:
        form.start_date.data = custom_start_date
    if end_date_param:
        form.end_date.data = custom_end_date
    form.event_format.data = event_format
    form.status.data = status
    form.tags.data = tags
    
    return render_template('main/calendar.html', 
                          title='Календарь мероприятий',
                          events=events,
                          month=month,
                          year=year,
                          prev_month=prev_month,
                          prev_year=prev_year,
                          next_month=next_month if 'next_month' in locals() else None,
                          next_year=next_year if 'next_year' in locals() else None,
                          calendar_days=calendar_days,
                          day_events_map=day_events_map,
                          month_names=month_names,
                          month_abbr=month_abbr,
                          weekdays=weekdays,
                          today=datetime.utcnow().date(),
                          form=form,
                          start_date=start_date,
                          end_date=end_date) 