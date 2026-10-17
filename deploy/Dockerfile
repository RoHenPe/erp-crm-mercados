FROM python:3.12-slim

WORKDIR /app

RUN pip install --no-cache-dir fastapi uvicorn[standard] sqlalchemy psycopg2-binary pydantic httpx pytest

COPY backend /app/backend
COPY frontend /app/frontend
COPY ARCHITECTURE.md /app/ARCHITECTURE.md

WORKDIR /app/backend
ENV PYTHONPATH=/app/backend
EXPOSE 8090

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8090"]
