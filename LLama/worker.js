export default {
  /**
   * Обрабатывает входящие HTTP запросы к Worker'у.
   * @param {Request} request - Объект входящего запроса.
   * @param {object} env - Переменные окружения и байндинги (включая AI).
   * @param {object} ctx - Контекст выполнения.
   * @returns {Promise<Response>} - Промис, который разрешается в объект Response.
   */
  async fetch(request, env, ctx) {
    // 1. Проверяем метод запроса (ожидаем POST)
    if (request.method !== 'POST') {
      return new Response('Ошибка: Ожидается метод POST', { status: 405 }); // Method Not Allowed
    }

    // 2. Проверяем наличие AI байндинга
    if (!env.AI) {
       console.error("AI Binding не настроен! Добавьте [[ai]] в wrangler.toml");
       return new Response('Ошибка конфигурации: AI Binding не найден.', { status: 500 });
    }

    // 3. Получаем тело запроса (ожидаем JSON)
    let requestBody;
    try {
      requestBody = await request.json();
    } catch (e) {
      console.error("Ошибка парсинга JSON:", e);
      return new Response('Ошибка: Некорректное тело запроса, ожидается JSON.', { status: 400 }); // Bad Request
    }

    // 4. Извлекаем сообщение пользователя и контекст событий
    const userMessage = requestBody.message;
    const eventsContextString = requestBody.events_context; // Ожидаем строку!

    if (!userMessage || typeof userMessage !== 'string' || userMessage.trim() === '') {
      return new Response('Ошибка: Отсутствует или некорректное поле "message" в JSON.', { status: 400 });
    }

    if (!eventsContextString || typeof eventsContextString !== 'string') {
       // Можно сделать контекст опциональным или вернуть ошибку
      return new Response('Ошибка: Отсутствует или некорректное поле "events_context" (ожидается строка) в JSON.', { status: 400 });
    }

    // 5. Формируем сообщения для модели Llama
    const messages = [
      {
        role: 'system',
        // Системный промпт: задаем роль и предоставляем контекст событий
        content: `Ты — полезный ИИ-ассистент. Тебе предоставлен список предстоящих IT-событий с Хабра. Основывай свои ответы на этом списке, но можешь использовать и общие знания, если вопрос выходит за рамки списка. Будь вежлив и информативен. Вот список событий:\n\n${eventsContextString}\n\nОтвечай на вопросы пользователя.`
      },
      {
        role: 'user',
        // Сообщение пользователя
        content: userMessage
      }
    ];

    // 6. Вызываем модель Llama 3 через Cloudflare AI
    try {
      console.log(`Вызов модели @cf/meta/llama-3-70b-instruct с сообщением: "${userMessage}"`);

      const aiResponse = await env.AI.run('@cf/meta/llama-3.3-70b-instruct-fp8-fast', {
        messages: messages,
        temperature: 0.3,   // Креативность (0 = детерминированно, 1 = макс. креативность)
        max_tokens: 1024,   // Максимальная длина ответа в токенах
        stream: false       // Установите true для потоковой передачи ответа (если нужно)
      });

      console.log("Ответ от AI получен.");

      // 7. Формируем и возвращаем ответ клиенту
      // Ожидаем, что ответ модели находится в поле 'response'
      const responseText = aiResponse.response || "Извините, модель не смогла сгенерировать ответ.";

      return new Response(JSON.stringify({ response: responseText }), {
        headers: { 'Content-Type': 'application/json' },
      });

    } catch (error) {
      console.error("Ошибка при вызове Cloudflare AI:", error);
      // Попытка извлечь более детальную информацию об ошибке, если она есть
      const errorMessage = error.message || "Неизвестная ошибка";
      const errorCause = error.cause ? JSON.stringify(error.cause) : "Нет деталей";
      return new Response(`Ошибка сервера при обработке AI запроса: ${errorMessage}. Причина: ${errorCause}`, { status: 500 });
    }
  },
};