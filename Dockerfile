
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1


RUN pip install --no-cache-dir uv


WORKDIR /app

COPY pyproject.toml uv.lock ./

RUN uv sync --no-install-project


COPY . .

RUN uv sync


ENV PATH="/app/.venv/bin:$PATH"

RUN python scripts/seed_db.py

EXPOSE 8000

CMD ["uvicorn", "scripts.api:app", "--host", "0.0.0.0", "--port", "8000"]