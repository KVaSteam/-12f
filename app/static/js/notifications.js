// Функция для получения уведомлений
function fetchNotifications() {
    fetch('/notifications')
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok: ' + response.statusText);
            }
            return response.json();
        })
        .then(data => {
            updateNotificationsUI(data.notifications, data.unread_count);
        })
        .catch(error => {
            console.error('Ошибка при получении уведомлений:', error);
            // Показываем сообщение об ошибке вместо загрузки
            const container = document.getElementById('notifications-container');
            container.innerHTML = `
                <div class="dropdown-item text-center text-muted">
                    <small>Не удалось загрузить уведомления</small>
                </div>
            `;
        });
}

// Функция обновления интерфейса уведомлений
function updateNotificationsUI(notifications, unreadCount) {
    const container = document.getElementById('notifications-container');
    const badgeElement = document.getElementById('notifications-count');
    
    // Обновляем счетчик непрочитанных уведомлений
    if (unreadCount > 0) {
        badgeElement.textContent = unreadCount;
        badgeElement.style.display = 'inline-block';
    } else {
        badgeElement.style.display = 'none';
    }
    
    // Очищаем контейнер
    container.innerHTML = '';
    
    // Если нет уведомлений
    if (notifications.length === 0) {
        container.innerHTML = `
            <div class="dropdown-item text-center text-muted">
                <small>У вас нет уведомлений</small>
            </div>
        `;
        return;
    }
    
    // Добавляем уведомления в контейнер
    notifications.forEach(notification => {
        const notificationElement = document.createElement('div');
        notificationElement.className = `dropdown-item notification-item ${notification.is_read ? '' : 'unread'}`;
        notificationElement.dataset.id = notification.id;
        
        // Выбираем иконку в зависимости от типа уведомления
        let icon = 'bell';
        if (notification.type === 'event_application') icon = 'user-plus';
        else if (notification.type === 'application_approved') icon = 'check-circle';
        else if (notification.type === 'application_rejected') icon = 'times-circle';
        else if (notification.type === 'event_approved') icon = 'thumbs-up';
        else if (notification.type === 'event_rejected') icon = 'thumbs-down';
        else if (notification.type === 'achievement_earned') icon = 'trophy';
        else if (notification.type === 'event_reminder') icon = 'calendar-alt';
        else if (notification.type === 'event_completed') icon = 'flag-checkered';
        
        // Форматирование времени
        const date = new Date(notification.created_at);
        const formattedDate = new Intl.DateTimeFormat('ru', {
            day: '2-digit',
            month: '2-digit',
            hour: '2-digit',
            minute: '2-digit'
        }).format(date);
        
        // Определяем URL для клика по уведомлению
        let targetUrl = '#';
        
        if (notification.related_id) {
            if (notification.type === 'event_application') {
                targetUrl = `/event/event/${notification.related_id}/applications`;
            } else if (notification.type === 'application_approved' || 
                      notification.type === 'application_rejected' || 
                      notification.type === 'event_approved' || 
                      notification.type === 'event_rejected' || 
                      notification.type === 'event_completed' || 
                      notification.type === 'event_reminder') {
                targetUrl = `/event/event/${notification.related_id}`;
            } else if (notification.type === 'achievement_earned') {
                targetUrl = `/profile/profile/${notification.related_id}`;
            }
        }
        
        notificationElement.innerHTML = `
            <div class="d-flex align-items-start notification-content" style="cursor: pointer;" onclick="handleNotificationClick(event, ${notification.id}, '${targetUrl}')">
                <div class="me-2">
                    <i class="fas fa-${icon} ${notification.is_read ? 'text-muted' : 'text-primary'}"></i>
                </div>
                <div class="flex-grow-1">
                    <div class="small ${notification.is_read ? 'text-muted' : 'fw-bold'}" style="white-space: normal; word-break: break-word;">${notification.content}</div>
                    <div class="text-muted smaller">${formattedDate}</div>
                </div>
                ${!notification.is_read ? `
                <div>
                    <button class="btn btn-sm mark-read" data-id="${notification.id}">
                        <i class="fas fa-check"></i>
                    </button>
                </div>` : ''}
            </div>
        `;
        
        container.appendChild(notificationElement);
    });
    
    // Добавляем обработчики для кнопок "прочитано"
    document.querySelectorAll('.mark-read').forEach(button => {
        button.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();
            const notificationId = button.dataset.id;
            markAsRead(notificationId);
        });
    });
}

// Обработчик клика по уведомлению (сначала отмечаем как прочитанное, затем переходим)
function handleNotificationClick(event, notificationId, targetUrl) {
    // Если клик был по кнопке "прочитано", ничего не делаем
    if (event.target.closest('.mark-read')) {
        return;
    }
    
    // Если уведомление не прочитано, отмечаем его прочитанным
    const notificationElement = document.querySelector(`.notification-item[data-id="${notificationId}"]`);
    if (notificationElement && notificationElement.classList.contains('unread')) {
        // Предотвращаем переход по ссылке до выполнения запроса
        event.preventDefault();
        
        markAsRead(notificationId, () => {
            // После успешной отметки переходим по ссылке
            if (targetUrl && targetUrl !== '#') {
                window.location.href = targetUrl;
            }
        });
    } else if (targetUrl && targetUrl !== '#') {
        window.location.href = targetUrl;
    }
}

// Получаем CSRF-токен из мета-тега
function getCsrfToken() {
    const metaTag = document.querySelector('meta[name="csrf-token"]');
    return metaTag ? metaTag.getAttribute('content') : '';
}

// Отмечаем уведомление как прочитанное
function markAsRead(notificationId, callback) {
    // Включаем CSRF-токен в запрос, если доступен
    const headers = {
        'Content-Type': 'application/json',
        'X-Requested-With': 'XMLHttpRequest'
    };
    
    const csrfToken = getCsrfToken();
    if (csrfToken) {
        headers['X-CSRFToken'] = csrfToken;
    }
    
    fetch(`/notifications/${notificationId}/read`, {
        method: 'POST',
        headers: headers,
        credentials: 'same-origin'
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Network response was not ok: ' + response.statusText);
        }
        return response.json();
    })
    .then(data => {
        if (data.success) {
            // Обновляем UI
            const notificationElement = document.querySelector(`.notification-item[data-id="${notificationId}"]`);
            if (notificationElement) {
                notificationElement.classList.remove('unread');
                const contentElement = notificationElement.querySelector('.fw-bold');
                if (contentElement) {
                    contentElement.classList.remove('fw-bold');
                    contentElement.classList.add('text-muted');
                }
                const iconElement = notificationElement.querySelector('.fas');
                if (iconElement) {
                    iconElement.classList.remove('text-primary');
                    iconElement.classList.add('text-muted');
                }
                const markReadButton = notificationElement.querySelector('.mark-read');
                if (markReadButton) {
                    markReadButton.parentElement.remove();
                }
            }
            
            // Обновляем счетчик
            const badge = document.getElementById('notifications-count');
            const currentCount = parseInt(badge.textContent);
            if (currentCount > 1) {
                badge.textContent = currentCount - 1;
            } else {
                badge.style.display = 'none';
            }
            
            // Вызываем callback, если передан
            if (typeof callback === 'function') {
                callback();
            }
        }
    })
    .catch(error => {
        console.error('Ошибка при отметке уведомления как прочитанное:', error);
        // Выводим более подробную информацию об ошибке
        fetch('/notifications')
            .then(res => res.json())
            .then(data => console.log('Текущие уведомления:', data));
    });
}

// Отмечаем все уведомления как прочитанные
function markAllAsRead() {
    // Включаем CSRF-токен в запрос, если доступен
    const headers = {
        'Content-Type': 'application/json',
        'X-Requested-With': 'XMLHttpRequest'
    };
    
    const csrfToken = getCsrfToken();
    if (csrfToken) {
        headers['X-CSRFToken'] = csrfToken;
    }
    
    fetch('/notifications/read-all', {
        method: 'POST',
        headers: headers,
        credentials: 'same-origin'
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Network response was not ok: ' + response.statusText);
        }
        return response.json();
    })
    .then(data => {
        if (data.success) {
            // Обновляем UI: удаляем класс unread у всех элементов
            document.querySelectorAll('.notification-item.unread').forEach(element => {
                element.classList.remove('unread');
                element.querySelector('.fw-bold')?.classList.replace('fw-bold', 'text-muted');
                element.querySelector('.text-primary')?.classList.replace('text-primary', 'text-muted');
                element.querySelector('.mark-read')?.parentElement.remove();
            });
            
            // Скрываем счетчик
            const badge = document.getElementById('notifications-count');
            badge.style.display = 'none';
        }
    })
    .catch(error => {
        console.error('Ошибка при отметке всех уведомлений как прочитанные:', error);
    });
}

// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', function() {
    // Получаем уведомления при загрузке страницы
    fetchNotifications();
    
    // Периодическое обновление каждую минуту
    setInterval(fetchNotifications, 60000);
    
    // Обработчик для кнопки "отметить все как прочитанные"
    document.getElementById('mark-all-read').addEventListener('click', markAllAsRead);
    
    // Стили для непрочитанных уведомлений
    const style = document.createElement('style');
    style.textContent = `
        .notification-item.unread {
            background-color: rgba(13, 110, 253, 0.05);
        }
        .smaller {
            font-size: 0.75rem;
        }
        .notification-content {
            width: 100%;
        }
        .notifications-menu {
            overflow-x: hidden !important;
        }
    `;
    document.head.appendChild(style);
}); 