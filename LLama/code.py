import requests
import json
import textwrap # Для красивого вывода ответа

# URL вашего развернутого Cloudflare Worker'а
WORKER_URL = "https://spring-union-aae1.bydymainit.workers.dev/"

def ask_ai_assistant(user_question: str, events_context_str: str, worker_url: str = WORKER_URL) -> str:
    """
    Отправляет запрос к Cloudflare Worker'у с вопросом и контекстом событий.

    Args:
        user_question: Вопрос пользователя.
        events_context_str: Строка, содержащая спарсенные события Habr.
        worker_url: URL Cloudflare Worker'а.

    Returns:
        Ответ от AI-ассистента или сообщение об ошибке.
    """
    payload = {
        "message": user_question,
        "events_context": events_context_str
    }
    headers = {
        "Content-Type": "application/json"
    }

    print(f"--- Отправка запроса на {worker_url} ---")
    print(f"Вопрос: {user_question}")
    # Не будем выводить весь контекст, он может быть большим
    print(f"Контекст событий: [передан, {len(events_context_str)} символов]")

    try:
        response = requests.post(worker_url, headers=headers, json=payload, timeout=60) # Увеличим таймаут для AI

        # Проверка кода состояния HTTP
        response.raise_for_status() # Вызовет исключение для кодов 4xx/5xx

        print(f"--- Ответ получен (Статус: {response.status_code}) ---")

        # Парсим JSON-ответ
        try:
            response_data = response.json()
            ai_response = response_data.get("response", "Ключ 'response' не найден в ответе JSON.")
            return ai_response
        except json.JSONDecodeError:
            print("Ошибка: Не удалось декодировать JSON из ответа.")
            print("Текст ответа:", response.text)
            return "Ошибка: Сервер вернул невалидный JSON."

    except requests.exceptions.Timeout:
        print("Ошибка: Запрос превысил время ожидания.")
        return "Ошибка: Превышено время ожидания ответа от сервера."
    except requests.exceptions.RequestException as e:
        print(f"Ошибка сети или HTTP: {e}")
        # Попробуем вывести тело ответа, если оно есть и содержит ошибку от воркера
        error_details = ""
        if hasattr(e, 'response') and e.response is not None:
             error_details = f" Детали от сервера: {e.response.status_code} - {e.response.text[:500]}" # Ограничим длину
        return f"Ошибка сети или HTTP при запросе к воркеру.{error_details}"
    except Exception as e:
        print(f"Произошла непредвиденная ошибка: {e}")
        return "Произошла непредвиденная ошибка при выполнении запроса."

# --- Пример использования ---
if __name__ == "__main__":
    # 1. Получите строку с событиями от вашего парсера
    # (Здесь пример строки, замените на реальные данные от парсера)
    habr_events_string = """
    Апрель
    1. Геймтон «DatsCity»
       Дата: 4 – 5 апреля
       Место: Онлайн
       Категории: Разработка
       Ссылка Habr: https://habr.com/ru/events/622/
       Сайт события: https://u.habr.com/cldr_datscity

    2. Конференция TEAMLY WORK MANAGEMENT 2025
       Дата: 8 апреля
       Место: Москва • Онлайн
       Категории: Менеджмент, Другое
       Ссылка Habr: https://habr.com/ru/events/626/
       Сайт события: https://u.habr.com/cldr_teamlyconf

    3. «GoCloud 2025» — масштабная IT-конференция про облака и AI
       Дата: 10 апреля
       Место: Москва • Онлайн
       Категории: Разработка, Администрирование, Менеджмент
       Ссылка Habr: https://habr.com/ru/events/590/
       Сайт события: https://u.habr.com/cldr_gocloud

    Июнь
    1. Летняя айти-тусовка Summer Merge
       Дата: 20 – 22 июня
       Место: Ульяновская область
       Категории: Разработка, Другое
       Ссылка Habr: https://habr.com/ru/events/610/
       Сайт события: https://u.habr.com/cldr_summermerge
    """

    # 2. Задайте ваш вопрос
    question = "Какие конференции по менеджменту пройдут в апреле в Москве?"
    # question = "Расскажи про летние мероприятия."
    # question = "Что такое геймтон?" # Вопрос не по списку

    # 3. Вызовите функцию
    answer = ask_ai_assistant(question, habr_events_string)

    # 4. Выведите ответ
    print("\n--- Ответ AI ---")
    # Используем textwrap для более аккуратного вывода длинных строк
    print(textwrap.fill(answer, width=80))
    print("---------------")