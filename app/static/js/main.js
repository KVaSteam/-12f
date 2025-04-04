// Общие функции JavaScript для приложения

// Инициализация всплывающих подсказок Bootstrap (tooltips)
document.addEventListener('DOMContentLoaded', function() {
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
});

// Инициализация всплывающих окон Bootstrap (popovers)
document.addEventListener('DOMContentLoaded', function() {
    var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    var popoverList = popoverTriggerList.map(function(popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
});

// Функция предварительного просмотра изображения перед загрузкой
function previewImage(input, previewElement) {
    if (input.files && input.files[0]) {
        var reader = new FileReader();
        
        reader.onload = function(e) {
            document.getElementById(previewElement).src = e.target.result;
        }
        
        reader.readAsDataURL(input.files[0]);
    }
}

// Функция для автоматического скрытия уведомлений через заданное время
window.setTimeout(function() {
    var alerts = document.querySelectorAll('.alert-dismissible');
    alerts.forEach(function(alert) {
        var bsAlert = new bootstrap.Alert(alert);
        bsAlert.close();
    });
}, 5000); // Автоматически скрывать уведомления через 5 секунд

/**
 * Инициализирует функцию очистки тегов в формах фильтрации
 */
function initTagClearFunctionality() {
    const clearTagsButton = document.getElementById('clear-tags');
    if (clearTagsButton) {
        clearTagsButton.addEventListener('click', function() {
            // Очищаем множественный выбор тегов
            const tagsSelect = document.getElementById('tags');
            if (tagsSelect) {
                for (let i = 0; i < tagsSelect.options.length; i++) {
                    tagsSelect.options[i].selected = false;
                }
            }
            
            // Отправляем форму для применения фильтра
            const filterForm = document.getElementById('filter-form');
            if (filterForm) {
                filterForm.submit();
            }
        });
    }
}

// Инициализируем все функции при загрузке страницы
document.addEventListener('DOMContentLoaded', function() {
    // Инициализация превью изображений
    initImagePreviews();
    
    // Инициализация функциональности очистки тегов
    initTagClearFunctionality();
});
