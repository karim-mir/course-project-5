FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y gcc build-essential libpq-dev curl \
  && apt-get clean && rm -rf /var/lib/apt/lists/*

RUN curl -sSL https://install.python-poetry.org | python3 -

ENV PATH="/root/.local/bin:$PATH"

COPY pyproject.toml poetry.lock ./

RUN poetry config virtualenvs.create false \
  && poetry install --no-root --only main --no-interaction --no-ansi -vvv

COPY . .

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
