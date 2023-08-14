FROM python:3.11.4-slim

ARG POETRY_VERSION=1.5.1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN python -m pip install poetry==${POETRY_VERSION}

COPY poetry.lock pyproject.toml ./

RUN poetry config virtualenvs.create false
RUN poetry install --no-interaction --no-ansi --no-root

COPY . .

ENTRYPOINT ["gunicorn"]

CMD ["--workers", "4", "--preload", "--bind", "0.0.0.0:8000", "api:app"]
