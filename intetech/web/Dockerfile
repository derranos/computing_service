# Используем базовый образ Python 3.9
FROM python:3.9-slim

# Устанавливаем рабочую директорию в контейнере
WORKDIR /app

# Копируем требования и устанавливаем зависимости
COPY ./server/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем сервер и веб-страницу в контейнер
COPY ./server /app/server
COPY ./web_page /app/web_page

# Открываем порт для FastAPI
EXPOSE 8000

# Запускаем сервер FastAPI
CMD ["uvicorn", "server.server:app", "--host", "0.0.0.0", "--port", "8000"]
