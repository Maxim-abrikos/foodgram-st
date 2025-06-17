FROM python:3.10
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt --no-cache-dir
COPY . .

RUN echo "#!/bin/bash\n\
# Применяем миграции\n\
python manage.py migrate\n\
# Собираем статику\n\
python manage.py collectstatic --no-input\n\
mv /app/collected_static/admin /app/collected_static/static/ \n\
mv /app/collected_static/rest_framework /app/collected_static/static/ \n\
# Запускаем Gunicorn\n\
exec gunicorn --bind 0.0.0.0:8000 foodgram.wsgi:application\n\
" > /entrypoint.sh && \
    chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]