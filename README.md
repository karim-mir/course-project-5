# О проекте
Этот проект реализует серверное приложение на Django с функционалом для работы с привычками (habits) и пользователями (users). Для запуска и управления сервисами используется Docker и Docker Compose.

# Структура проекта:

- habits/ — основное Django приложение для управления привычками

- users/ — Django приложение для работы с пользователями

- config/ — конфигурационные файлы Django (settings, urls, wsgi, asgi)

- deploy/ — файлы для деплоя (например, docker-compose.yaml)

- static/ — собранные статические файлы

- nginx.conf — конфигурация Nginx для обратного прокси

- Dockerfile — описание сборки Docker-образа backend

- docker-compose.yaml — описание сервисов в Docker Compose

- .env и .env.example — файлы с настройками окружения

- manage.py — точка входа в Django проект

- poetry.lock, pyproject.toml — конфигурация зависимостей Poetry

- tests/ внутри приложений — тесты для кода приложений

# Технологии:
- Python 3.12

- Django

- PostgreSQL

- Redis

- Celery

- Poetry для управления зависимостями

- Docker и Docker Compose для контейнеризации

- Nginx для обратного прокси и отдачи статики

## Установка и запуск
1. Клонировать репозиторий:
```commandline
git clone <url>
cd CourseProject5
```
2. Создать файл .env на основе .env.example и заполнить необходимые переменные окружения.

3. Запустить сборку и запуск контейнеров Docker:
```
docker compose up -d --build
```
4. Выполнить миграции Django:
```commandline
docker compose exec backend python manage.py migrate
```
5. Собрать статические файлы:
```commandline
docker compose exec backend python manage.py collectstatic --noinput
```

## Запуск тестов
```commandline
docker compose exec backend pytest
```
### Полезные команды
1. Остановить контейнеры:
```
docker compose down
```
2. Просмотр логов:
```commandline
docker compose logs -f
```

### Dockerfile
- Описание процесса сборки backend-образа с `Python 3.12` и `Poetry`.

- Используется официальный образ `python:3.12-slim`.

- Устанавливаются необходимые системные библиотеки (`gcc`, `build-essential`, `libpq-dev`, `curl`) для сборки зависимостей и работы с `PostgreSQL`.

- Скачивается и устанавливается `Poetry` в папку `/opt/poetry`.

- Создается системный пользователь app с домашней директорией `/home/app`.

- Создаются необходимые папки `/home/app`, `/app`, `/app/static` с правами пользователя app.

- Рабочей директорией контейнера назначается `/app`.

- Проект и файлы зависимостей `pyproject.toml` и `poetry.lock` копируются в контейнер с правильными владельцами.

- Poetry устанавливает зависимости, используя опцию `--no-root` и устанавливая только основные зависимости.

- Копируется остальной код проекта.

- Контейнер запускает `Django develop` сервер командой: ```python manage.py runserver 0.0.0.0:8000``` от пользователя `app`.

### Docker Compose
В конфигурации `Docker Compose` определены следующие сервисы:

- `db` — контейнер с `PostgreSQL`, с настройкой переменных окружения через `.env` и хранением данных в `volume pg_data`. Имеется `healthcheck` для проверки готовности базы.

- `redis` — контейнер с `Redis` для брокера сообщений `Celery`, также с `healthcheck`.

- `backend` — образ, строящийся из `Dockerfile`, запускающий миграции и затем `Django runserver` на порту 8000. Использует переменные окружения из `.env`. Зависит от `db` и `redis`.

- `static_collector` — контейнер для сбора статических файлов `Django` (команда `collectstatic`), с `volume` для сохранения статики `django_static`. Запускается без перезапуска.

- `celery_worker` — запускает `Celery worker` для обработки фоновых задач. Зависит от `db` и `redis`.

- `celery_beat`— запускает `Celery beat` для периодических задач с хранением расписания.

- `web` — контейнер с `Nginx`, который зависит от `backend` и `static_collector`. Монтируется локальный файл `nginx.conf` в контейнер и `shared volume django_static` для отдачи статики. Слушает 80 порт.

#### Volumes
- `pg_data` — хранит данные `PostgreSQL`.

- `django_static` — хранит собранные статические файлы.

- `celery_beat_data` — подкачка для расписания `Celery beat`.

### Полезные команды Docker Compose
1. Запустить все сервисы в фоне с созданием образов и миграциями:

```
docker compose up -d --build
docker compose exec backend python manage.py migrate
```
2. Чтобы собрать статику (обычно автоматически выполняется в `static_collector`):
```
docker compose exec static_collector
```
3.Посмотреть логи сервиса:
```
docker compose logs -f backend
```
4. Остановить все сервисы и удалить `volumes`:
```
docker compose down -v
```

### Конфигурация Nginx (обратный прокси)
`Nginx` настроен для работы в качестве обратного прокси-сервера перед вашим Django-приложением. Такая конфигурация позволяет:

- Обеспечить доступ к проекту по стандартному HTTP-порту 80.

- Отдавать статические файлы непосредственно через `Nginx` для повышения производительности.

- Передавать остальные HTTP-запросы приложению Django на backend-сервер, который работает на порту 8000.

Основные настройки `Nginx`:

```
upstream django_backend {
    server backend:8000;
}

server {
    listen 80;

    root /usr/share/nginx/html;
    index index.html;

    location /static/ {
        root /usr/share/nginx/html/;
    }

    location / {
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header Host $http_host;
        proxy_pass http://django_backend;
    }
}
```
- ``upstream django_backend`` — это блок, который определяет адрес `Django backend` в сети `Docker` (сервис с именем backend на порту 8000).

- `location /static/` направляет запросы на отдачу статических файлов из папки `/usr/share/nginx/html/static` (которая синхронизируется с Django-статикой).

Запросы на корневой путь / проксируются на `Django backend`.

В прокси-запросы добавляются важные заголовки для правильной обработки IP клиента и хостовой информации в `Django`.

### Переменные окружения (.env)
Для настройки проекта используется файл `.env`, в котором хранятся конфиденциальные и специфичные для среды значения. В проекте есть пример `.env.example` с набором следующих переменных:

#### Настройки базы данных PostgreSQL

`POSTGRES_DB` — имя базы данных

`POSTGRES_USER` — пользователь базы данных

`POSTGRES_PASSWORD` — пароль базы

`POSTGRES_PORT` — порт для подключения

`POSTGRES_HOST` — хост базы данных

#### Основные настройки Django
`SECRET_KEY` — секретный ключ `Django` (обязательно для `production`)

`DEBUG` — режим отладки (`True` или `False`)

`TIME_ZONE` — часовой пояс

#### Настройки Redis
`REDIS_URL` — `URL Redis` сервера (брокер для `Celery`)

#### Настройки Celery
`CELERY_BROKER_URL` — `URL` брокера сообщений

`CELERY_RESULT_BACKEND` — `backend` для хранения результатов задач

`CELERY_BEAT_SCHEDULE_FILENAME` — имя файла с расписанием периодических задач `Celery Beat`

#### Настройки Telegram-бота
`TELEGRAM_BOT_TOKEN` — токен для `Telegram Bot API`

#### Как использовать .env
1. Создайте файл `.env` на основе `.env.example` и заполните значения переменных.

2. Файл `.env` должен находиться в корне проекта, на одном уровне с `manage.py`.

3. Файл не должен попадать в систему контроля версий (должен быть в `.gitignore`).

4. В вашем `settings.py` или конфигурации `Django` должен быть подключен пакет `python-dotenv` или `django-environ` для загрузки переменных из `.env`.

### Конфигурация Django
Настройки `Django` загружаются с использованием пакета `python-dotenv`:
```
python
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv("SECRET_KEY")
DEBUG = os.getenv("DEBUG", "False") == "True"

ALLOWED_HOSTS = ["*"]  # Можно настроить под реальные хосты

DATABASES = {
    "default": {
        "ENGINE": os.getenv("DB_ENGINE", "django.db.backends.postgresql_psycopg2"),
        "NAME": os.getenv("DB_NAME", ""),
        "USER": os.getenv("DB_USER", ""),
        "PASSWORD": os.getenv("DB_PASSWORD", ""),
        "HOST": os.getenv("DB_HOST", "db"),
        "PORT": os.getenv("DB_PORT", ""),
    }
}

STATIC_URL = "static/"
STATIC_ROOT = Path("/app/static")

CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/1")

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
```
- Пакет `python-dotenv` загружает переменные из файла `.env`.

- Важные параметры (секретный ключ, режим отладки, база данных, брокер и бекенд `Celery`) подтягиваются из окружения.

- Путь к статическим файлам и прочие настройки адаптированы для работы с `Docker` и `Nginx`.

- Используется кастомная модель пользователя `users.User`.

Таким образом проект гибко конфигурируется под разные среды (разработка, тестирование, продакшен) через файл `.env` без изменения кода.

## Основные модели
### Habit
Модель `Habit` описывает привычку пользователя со следующими ключевыми полями:

- `user` — пользователь, которому принадлежит привычка (может быть пустым).

- `place` — место, где выполняется привычка.

- `time` — время, когда привычка выполняется.

- `action` — описание действия привычки.

- `is_pleasant_habit` — признак, что привычка является приятной.

- `associated_habits` — связанные с этой привычкой другие привычки.

- `periodicity` — периодичность повторения (в днях).

- `reward` — вознаграждение за выполнение привычки.

- `time_to_complete` — предполагаемое время выполнения.

- `is_public` — признак публичности привычки.

Модель имеет метод `clean`, который выполняет валидацию и очистку данных, и метод `__str__`, который возвращает читаемое представление привычки.

### User
Для расширения стандартной модели пользователя Django в проекте реализована кастомная модель `User`, которая наследует `AbstractUser` и использует `email` в качестве уникального идентификатора вместо `username`.

#### Основные особенности:
1. Поле `email` является уникальным и обязательным для аутентификации.

2. Нет поля `username`, так как аутентификация происходит по `email`.

#### Дополнительные поля:

- `telegram_chat_id` — для связи с Telegram-ботом и отправки уведомлений.

- `avatar` — загружаемый аватар пользователя.

- `phone` — номер телефона с валидацией через `PhoneNumberField`.

- `city` — город пользователя.

- `token` — дополнительное поле для хранения токена (по назначению проекта).

##### Менеджер пользователей
Класс `UserManager` реализует методы `create_user` и `create_superuser`, обеспечивая корректное создание пользователей с `email` и необходимыми правами.

Проверяется обязательное наличие `email` при создании пользователя.

Для суперпользователя гарантируются флаги `is_staff=True`, `is_superuser=True` и `is_active=True`.

Конфигурация
В `settings.py` указывается:
```commandline
AUTH_USER_MODEL = "users.User"
```
Это позволяет `Django` использовать кастомную модель пользователя вместо стандартной.

### Запуск Telegram-бота
Для взаимодействия с пользователями через `Telegram` в проекте реализован Telegram-бот, который умеет:

- Регистрировать пользователя по `email`.

- Показывать список привычек пользователя.

- Добавлять новую привычку.

- Удалять привычки через интерактивные кнопки.

- Выводить справочную информацию по командам.

#### Основные команды бота
`/start` — приветствие и инструкция по регистрации.

`/register <email>` — привязать аккаунт Django к Telegram чату.

`/habits`— показать текущие привычки.

`/addhabit <название> <время (ЧЧ:ММ)> <длительность (ЧЧ:ММ:СС)>` — добавить новую привычку.

`/help` — показать справку по командам.

#### Особенности реализации
Бот написан с использованием библиотеки `python-telegram-bot` с поддержкой асинхронности.

Команды бота обрабатывают запросы, взаимодействуют с базой `Django` через асинхронные вызовы.

Для запуска токен бота подгружается из переменной окружения `TELEGRAM_BOT_TOKEN`.

Поддерживается удаление привычек через клавиатуру с инлайн-кнопками.

Запуск бота осуществляется командой `Django management`, например, через кастомный командный скрипт:

```commandline
python manage.py telegram_bot
```
(где `telegram_bot` — название команды из вашего скрипта `BaseCommand`).

#### Рекомендации
- Бот должен запускаться отдельно от основного `Django` web-сервера.

- Используйте докер или `supervisor` для менеджмента процесса бота в продакшене.

- Переменная `TELEGRAM_BOT_TOKEN` указывается в .env для безопасности.

## Контакты

Если возникли вопросы, обращайтесь к *karimov.jalil@mail.ru*.