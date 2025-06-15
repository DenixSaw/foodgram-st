FROM python:3.9-slim

WORKDIR /app


RUN apt-get update && \
    apt-get install -y python3 build-essential zlib1g-dev libjpeg-dev libfreetype6-dev libpq-dev && \
    rm -rf /var/lib/apt/lists/*

RUN pip install gunicorn==20.1.0

COPY requirements.txt /app/

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["sh", "-c", "python manage.py migrate && python manage.py collectstatic --noinput && gunicorn core.wsgi:application --bind 0.0.0.0:8000"]