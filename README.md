Foodgram - Российское приложение для любителей кушать и готовить!
Что это такое?
Foodgram - это платформа, где каждый может делиться своими рецептами, добавлять понравившиеся блюда в избранное, следить за кулинарными авторами и составлять список покупок для выбранных рецептов.

Проект представляет собой REST API, упакованный в Docker для простого и быстрого развертывания.

Что использовалось:  
- Python  
- Django  
- Django REST Framework  
- PostgreSQL (было желание перепрыгнуть на MySQL)  
- Nginx  
- Docker  
- GitHub Actions (для CI/CD)  
  
Требования
Установленный Docker
Docker Compose
Как использовать: 
1. Клонируйте репозиторий (реквизируйте)
git clone https://github.com/Maxim-abrikos/foodgram-st.git
cd foodgram-st
Или просто скачайте .zip прямо с сайта ГитХаба
3. Настройка .env
Создайте файл .env в корневой папке проекта и заполните его следующими переменными:

DB_ENGINE=django.db.backends.postgresql  
DB_NAME=foodgram  
DB_USER=foodgram_user  
DB_PASSWORD=foodgram_password  
DB_HOST=db  
DB_PORT=5432  

3. Запуск проекта
docker-compose up --build # Сборка и запуск контейнеров

И на этом всё
Foodgram готов к работе, дерзайте!
