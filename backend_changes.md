# Изменения на бэкенде для подключения фронтенда

## 1\. Разрешить CORS

Без этого браузер заблокирует запросы фронтенда к API (разные origin: файл/localhost для фронта, `127.0.0.1:8000` для Django).

```bash
pip install django-cors-headers
```

В `requirements.txt`:

```
django-cors-headers
```

В `settings.py`:

```python
INSTALLED\_APPS = \[
    ...
    'corsheaders',
]

MIDDLEWARE = \[
    'corsheaders.middleware.CorsMiddleware',   # должен быть выше CommonMiddleware
    'django.middleware.common.CommonMiddleware',
    ...
]

# на время разработки — разрешить всё:
CORS\_ALLOW\_ALL\_ORIGINS = True

# для продакшена лучше явный список:
# CORS\_ALLOWED\_ORIGINS = \[
#     "http://localhost:5500",
#     "https://твой-домен-фронтенда",
# ]
```

## 2\. Проверь фактические форматы ответов API

Фронтенд (`frontend/index.html`) написан по документированной структуре проекта (`requests.http`), но точные ключи в JSON могут отличаться от того, что я предположил. Особенно проверь в консоли браузера (F12 → Network) ответы этих запросов при первом тесте:

|Запрос|Что фронтенд ожидает|Где поправить, если не совпадает|
|-|-|-|
|`POST /api/user/login`|поле `Token` или `token` с токеном авторизации|`pick(data, \['Token','token','auth\_token'])` в `<script>`|
|`GET /api/products`|список товаров с полями `id, name, model, price, price\_rrc, quantity, shop\_name`|функция `renderGrid()`|
|`POST /api/basket` → `GET/POST /api/order`|двухшаговое оформление: сначала корзина, потом заказ с `contact`|обработчик `#placeOrderBtn`|

Если у тебя в проекте эндпоинты называются иначе или поля другие — эти места в JS изолированы и их легко подправить под реальный ответ, не трогая остальной код.

## 3\. Как запустить связку локально

```bash
# терминал 1 — backend
cd django\_retail\_chain
python manage.py runserver

# терминал 2 — frontend (просто раздать статику)
cd frontend
python -m http.server 5500
```

Открой `http://localhost:5500`, в поле "API base URL" оставить `http://127.0.0.1:8000/api` (или поправить под свой порт).

