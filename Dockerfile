FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    AIM_DATA_DIR=/data

WORKDIR /app

COPY pyproject.toml README.md ./
COPY configs ./configs
COPY src ./src

RUN pip install --no-cache-dir .

EXPOSE 8765

CMD ["python", "-m", "ai_management.server"]
