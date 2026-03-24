FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install dependencies first (better caching)
COPY requirements.txt .
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Go where manage.py actually is
WORKDIR /app/stockee

EXPOSE 8000

CMD ["sh", "-c", "\
if [ \"$DJANGO_ENV\" = 'prod' ]; then \
    echo 'Starting Gunicorn for production'; \
    gunicorn stockee.wsgi:application --bind 0.0.0.0:8000 --workers 3; \
else \
    echo 'Starting Django dev server'; \
    python manage.py runserver 0.0.0.0:8000; \
fi \
"]
