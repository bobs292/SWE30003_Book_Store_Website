# syntax=docker/dockerfile:1
FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY . .

RUN pip install --no-cache-dir -e . \
    && pip install --no-cache-dir gunicorn

EXPOSE 8000

# create_app() runs init_db() at import: creates the SQLite file, seeds
# books, and fetches covers from Open Library. needs network on first start.
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "1", "src.app:app"]
