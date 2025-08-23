FROM python:3.12-slim

# Установка необходимых пакетов
RUN apt-get update && apt-get install -y gcc build-essential libpq-dev curl \
  && apt-get clean && rm -rf /var/lib/apt/lists/*

# Установка Poetry в /opt/poetry
ENV POETRY_HOME="/opt/poetry"
ENV PATH="$POETRY_HOME/bin:$PATH"

RUN curl -sSL https://install.python-poetry.org | python3 -

# Создаем пользователя app с домашней директорией /home/app
RUN addgroup --system app && adduser --system --group app --home /home/app

# Создаем домашнюю и рабочую директории с правильными владельцами
RUN mkdir -p /home/app /app /app/static && chown -R app:app /home/app /app /app/static

# Меняем владельца Poetry на пользователя app
RUN chown -R app:app $POETRY_HOME

WORKDIR /app

# Переключаемся на пользователя app
USER app

# Добавляем локальный poetry/bin и pip скрипты в PATH
ENV PATH="/home/app/.local/bin:$PATH"

# Копируем pyproject.toml и poetry.lock файлы, даем права
COPY --chown=app:app pyproject.toml poetry.lock ./

# Устанавливаем зависимости
RUN poetry config virtualenvs.create false && poetry install --no-root --only main --no-interaction --no-ansi -vvv

# Копируем остальной код с нужными правами
COPY --chown=app:app . .

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
