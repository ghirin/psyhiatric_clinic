// Горячие клавиши и быстрый поиск для всех страниц

document.addEventListener('DOMContentLoaded', function() {
    // Функция для показа модального окна быстрого поиска
    window.showQuickSearch = function() {
        const modalEl = document.getElementById('quickSearchModal');
        if (modalEl) {
            const modal = new bootstrap.Modal(modalEl);
            modal.show();
            setTimeout(() => {
                const input = document.getElementById('quickSearchInput');
                if (input) input.focus();
            }, 100);
        }
    };

    // Навесить обработчик на ссылку поиска (без inline-скрипта)
    const searchLinks = document.querySelectorAll('a[data-hotkey-search]');
    searchLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            window.showQuickSearch();
        });
    });

    // Горячие клавиши
    document.addEventListener('keydown', function(e) {
        // Игнорировать ввод в полях
        if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA' || e.target.isContentEditable) {
            if (e.key !== '?' || e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') {
                return;
            }
        }
        if (e.target.closest && e.target.closest('.modal')) return;
        const key = e.key.toUpperCase();
        if (e.ctrlKey || e.metaKey) return;
        switch(key) {
            case 'N':
                e.preventDefault();
                window.location.href = window.hotkeyUrls?.create || '/patients/create/';
                break;
            case 'S':
                e.preventDefault();
                window.showQuickSearch();
                break;
            case 'C':
                e.preventDefault();
                window.location.href = window.hotkeyUrls?.calendar || '/patients/calendar/';
                break;
            case 'E':
                e.preventDefault();
                window.location.href = window.hotkeyUrls?.export || '/patients/export/';
                break;
            case 'H':
                e.preventDefault();
                window.location.href = window.hotkeyUrls?.dashboard || '/';
                break;
            case '?':
                e.preventDefault();
                const helpAlert = document.createElement('div');
                helpAlert.className = 'alert alert-info position-fixed bottom-0 end-0 m-3';
                helpAlert.style.zIndex = '9999';
                helpAlert.innerHTML = `
                    <strong>Горячие клавиши:</strong><br>
                    N - Новый пациент<br>
                    S - Поиск пациента<br>
                    C - Календарь<br>
                    E - Экспорт<br>
                    H - Дашборд<br>
                    ? - Эта справка
                    <button type="button" class="btn-close position-absolute top-0 end-0 m-1" onclick="this.parentElement.remove()"></button>
                `;
                document.body.appendChild(helpAlert);
                setTimeout(() => helpAlert.remove(), 5000);
                break;
        }
    });
});
