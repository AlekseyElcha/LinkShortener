console.log('=== app.js загружен ===');

// Функция отображения страницы статистики
function showStatisticsPage(slug, redirects) {
    console.log('=== showStatisticsPage вызвана ===');
    console.log('Slug:', slug);
    console.log('Redirects:', redirects);
    console.log('Redirects type:', typeof redirects);
    console.log('Is array:', Array.isArray(redirects));
    
    // Скрываем все страницы
    document.getElementById('main-page').style.display = 'none';
    document.getElementById('login-page').style.display = 'none';
    document.getElementById('register-page').style.display = 'none';
    document.getElementById('dashboard-page').style.display = 'none';
    document.getElementById('statistics-page').style.display = 'block';
    
    console.log('Страница статистики показана');
    
    // Заполняем информацию о ссылке
    const shortUrl = window.location.origin + '/' + slug;
    document.getElementById('stats-short-url').innerHTML = `<a href="${shortUrl}" target="_blank">${shortUrl}</a>`;
    
    // Получаем оригинальную ссылку из первого элемента
    const longUrl = redirects && redirects.length > 0 ? redirects[0].long_url : 'Неизвестно';
    document.getElementById('stats-long-url').textContent = longUrl;
    
    console.log('Long URL:', longUrl);
    
    // Количество переходов
    const totalClicks = redirects ? redirects.length : 0;
    document.getElementById('stats-total-clicks').textContent = totalClicks;
    
    console.log('Total clicks:', totalClicks);
    
    // Отображаем список переходов
    displayStatisticsList(redirects);
    
    console.log('=== showStatisticsPage завершена ===');
}

// Функция отображения списка переходов
function displayStatisticsList(redirects) {
    const container = document.getElementById('statistics-list');
    if (!container) return;

    if (!redirects || redirects.length === 0) {
        container.innerHTML = '<div class="statistics-empty">Переходов пока не было</div>';
        return;
    }

    let html = '';
    redirects.forEach((redirect, index) => {
        const time = redirect.time || 'Неизвестно';
        const userId = redirect.created_by || 'Неизвестно';
        
        html += `
            <div class="statistics-item">
                <div class="statistics-number">#${index + 1}</div>
                <div class="statistics-details">
                    <div class="statistics-time">Время: ${time}</div>
                    <div class="statistics-user">ID пользователя: ${userId}</div>
                </div>
            </div>
        `;
    });

    container.innerHTML = html;
}

// Функция отображения детальной истории переходов
async function showRedirectHistory(slug) {
    console.log('Запрос истории для slug:', slug);
    try {
        const response = await fetch(`/slug_redirect_history/${slug}`, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
            }
        });

        console.log('Статус ответа:', response.status);
        console.log('Response OK:', response.ok);

        if (response.ok) {
            const data = await response.json();
            console.log('История переходов для slug:', slug);
            console.log('Полученные данные:', JSON.stringify(data, null, 2));
            console.log('Тип данных:', typeof data);
            console.log('Это массив?', Array.isArray(data));
            
            // Переходим на отдельную страницу статистики
            showStatisticsPage(slug, data);
        } else {
            console.error('Ошибка загрузки истории переходов:', response.status);
            const errorText = await response.text();
            console.log('Ответ сервера:', errorText);
            alert('Ошибка загрузки истории переходов. Статус: ' + response.status);
        }
    } catch (error) {
        console.error('Ошибка при загрузке истории переходов:', error);
        console.error('Тип ошибки:', error.name);
        console.error('Сообщение ошибки:', error.message);
        console.error('Stack trace:', error.stack);
        alert('Ошибка соединения с сервером: ' + error.message);
    }
}

// Функция возврата к личному кабинету
function backToDashboard() {
    showDashboard();
    // Обновляем историю
    loadUrlHistory('dashboard-history-list');
}

console.log('=== Все функции статистики определены ===');
console.log('showStatisticsPage:', typeof showStatisticsPage);
console.log('showRedirectHistory:', typeof showRedirectHistory);
