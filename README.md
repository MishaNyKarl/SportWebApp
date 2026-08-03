# SportWebApp

Django-приложение для тренировок: таймер отдыха, счётчик повторений, часы/секундомер,
статистика и напоминания. Дизайн — светлый, "стеклянный" iOS-стиль (Liquid Glass),
мобильный вид под iPhone (safe-area, нижний таб-бар, крупные заголовки).

## Локальный запуск

```bash
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

Открой http://127.0.0.1:8000 — лучше всего смотреть в мобильном режиме браузера
(DevTools → эмуляция iPhone).

Админка: http://127.0.0.1:8000/admin/ (сначала `python manage.py createsuperuser`).

## Запуск через Docker (как на проде)

```bash
cp .env.example .env   # заполни секреты
docker compose up -d --build
```

Приложение будет на http://localhost.

## Структура

- `sportapp/` — настройки Django-проекта
- `tracker/` — основное приложение (модели, вьюхи, формы, админка)
- `templates/` — HTML-шаблоны (`base.html` + страницы `tracker/*.html`)
- `static/tracker/` — CSS и JS (vanilla JS, без сборщиков)
- `deploy/` — Dockerfile-обвязка, nginx.conf, скрипт настройки сервера,
  инструкция по деплою (`deploy/README-deploy.md`)
- `.github/workflows/deploy.yml` — CI/CD: проверка + автодеплой на сервер по push в `main`

## Деплой

См. [`deploy/README-deploy.md`](deploy/README-deploy.md) — пошаговая настройка
сервера, GitHub Secrets и автодеплоя.
