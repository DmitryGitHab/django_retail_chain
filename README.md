# 🛒 Retail Chain API — сервис заказа товаров для розничных сетей

Дипломный проект курса «Python-разработчик». REST API-сервис для автоматизации закупок в розничной сети: менеджеры закупок формируют заказы по каталогу товаров сразу от нескольких поставщиков, а поставщики управляют своим прайс-листом и получают заказы.

## Содержание
- [Возможности](#возможности)
- [Архитектура и стек](#архитектура-и-стек)
- [Модель данных](#модель-данных)
- [Быстрый старт](#быстрый-старт)
- [API](#api)
- [Импорт прайса поставщика](#импорт-прайса-поставщика)
- [Структура проекта](#структура-проекта)
- [Что можно улучшить дальше](#что-можно-улучшить-дальше)

## Возможности

**Покупатель (менеджер закупок):**
- Регистрация, подтверждение email, вход по токену, восстановление пароля
- Просмотр каталога товаров с фильтрацией по магазину/категории
- Формирование корзины из товаров разных поставщиков в одном заказе
- Управление адресами доставки (контакты)
- Оформление заказа и просмотр истории заказов

**Поставщик:**
- Импорт/обновление прайс-листа через YAML-файл (по URL)
- Включение и отключение приёма заказов
- Просмотр заказов, содержащих товары из своего прайса

## Архитектура и стек

- **Backend:** Python 3, Django 4, Django REST Framework
- **Auth:** DRF Token Authentication
- **База данных:** SQLite для разработки (легко переключается на PostgreSQL через `django-environ`)
- **Импорт данных:** YAML (прайс-листы поставщиков)
- **Уведомления:** email (подтверждение регистрации, восстановление пароля)

## Модель данных

```
User (кастомная модель, type: buyer/shop)
 ├── Contact (адреса доставки, many-to-one)
 └── Order (many-to-one)
      └── OrderItem (many-to-one → ProductInfo)

Shop
 └── ProductInfo (позиция товара конкретного магазина: цена, остаток)
      ├── Product (→ Category)
      └── ProductParameter (→ Parameter, характеристики товара)
```

## Быстрый старт

```bash
git clone https://github.com/DmitryGitHab/django_retail_chain.git
cd django_retail_chain

python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

pip install -r requirements.txt
cp .env.example .env            # заполни своими значениями, см. ниже

python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Сервер поднимется на `http://127.0.0.1:8000/`.

### Переменные окружения (`.env`)

```
SECRET_KEY=django-insecure-change-me
DEBUG=True
EMAIL_HOST_USER=your@email.com
EMAIL_HOST_PASSWORD=app-password
```

> Проект использует `django-environ` — не храни `SECRET_KEY` и пароли в `settings.py`, только в `.env` (файл не должен попадать в git).

## API

Полный набор запросов с примерами — в [`requests.http`](./requests.http) (можно выполнять прямо из PyCharm/VS Code REST Client).

| Метод | Эндпоинт | Описание | Auth |
|---|---|---|---|
| POST | `/api/user/register` | Регистрация пользователя | — |
| POST | `/api/user/register/confirm` | Подтверждение email по токену | — |
| POST | `/api/user/login` | Вход, получение auth-токена | — |
| GET/POST | `/api/user/details` | Просмотр/редактирование профиля | Token |
| GET | `/api/categories` | Список категорий товаров | — |
| GET | `/api/shops` | Список магазинов | — |
| GET | `/api/products` | Каталог товаров | — |
| GET/POST/PUT/DELETE | `/api/user/contact` | Адреса доставки | Token |
| GET/POST/PUT/DELETE | `/api/basket` | Корзина | Token |
| GET/POST | `/api/partner/state` | Статус приёма заказов поставщиком | Token |
| POST | `/api/partner/update` | Импорт прайса из YAML | Token |
| GET | `/api/partner/orders` | Заказы по товарам поставщика | Token |
| GET/POST | `/api/order` | Оформление / список заказов | Token |

## Импорт прайса поставщика

Поставщик присылает `POST /api/partner/update` со ссылкой на YAML-файл вида:

```yaml
shop: shop_1
categories:
  - id: 224
    name: Смартфоны
goods:
  - id: 554563
    category: 224
    model: apple/iphone/xr
    name: Смартфон Samsung A10 (синий)
    price: 40000
    price_rrc: 43990
    quantity: 45
    parameters:
      "Диагональ (дюйм)": 6.1
      "Встроенная память (Гб)": 64
```

Пример файла — [`data/shop2.yaml`](./data/shop2.yaml).

## Структура проекта

```
django_retail_chain/
├── api_shop/              # основное DRF-приложение: модели, views, сериализаторы
├── django_retail_chain/   # настройки проекта Django
├── data/                  # примеры YAML-прайсов для импорта
├── requests.http          # готовые запросы для ручного тестирования API
├── manage.py
└── requirements.txt
```

## Фронтенд (Order Desk)

В папке [`frontend/`](./frontend/index.html) — лёгкий одностраничный интерфейс на чистом HTML/CSS/JS (без сборки, без npm), который обращается к этому API напрямую: каталог с фильтрами, корзина, оформление заказа, история заказов.

```bash
# backend
python manage.py runserver

# frontend — в отдельном терминале
cd frontend
python -m http.server 5500
```

Открой `http://localhost:5500`. Не забудь включить CORS на бэкенде — см. [`backend_changes.md`](./backend_changes.md).

> Сделай скриншот работающего каталога и вставь сюда `![Order Desk](./frontend/screenshot.png)` — живая картинка в README сильно поднимает доверие HR к проекту.

## Что можно улучшить дальше

- [ ] Покрыть ключевые сценарии тестами (pytest-django)
- [ ] Автогенерируемая документация API (drf-spectacular / Swagger)
- [ ] Docker + docker-compose (PostgreSQL вместо SQLite)
- [ ] CI на GitHub Actions (линт + тесты на каждый PR)
- [ ] Пагинация и фильтрация в `/api/products`
