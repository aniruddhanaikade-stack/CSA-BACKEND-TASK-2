FROM python:3.12-slim

WORKDIR /app

# install packages first (faster rebuilds)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# copy the project
COPY . .

# the database file lives in /data, which is a Docker volume
ENV DB_PATH=/data/db.sqlite3
ENV PYTHONUNBUFFERED=1
RUN mkdir -p /data

EXPOSE 8000

# create/update tables, then start the web server
CMD ["sh", "-c", "python manage.py migrate && gunicorn config.wsgi --bind 0.0.0.0:8000 --workers 2"]
