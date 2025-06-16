from django.contrib.auth.models import AbstractUser
from django.db import models

# Наследуемся от стандартного юзера Django, чтобы добавить свои поля
class User(AbstractUser):
    email = models.EmailField(max_length=254, unique=True)  # Уникальная почта — логин будет по ней
    username = models.CharField(max_length=150, unique=True)  # Уникальное имя пользователя
    first_name = models.CharField(max_length=150)  # Имя
    last_name = models.CharField(max_length=150)  # Фамилия
    avatar = models.ImageField(upload_to='users/avatars/', null=True, blank=True)  # Фото профиля (необязательно)

    class Meta:
        ordering = ['username']  # По умолчанию сортируем по юзернейму

    def __str__(self):
        return self.username  #просто имя пользователя

# Модель подписки одного пользователя на другого
class Subscription(models.Model):
    user = models.ForeignKey(User, related_name='subscriptions', on_delete=models.CASCADE)  # Подписчик
    author = models.ForeignKey(User, related_name='subscribers', on_delete=models.CASCADE)  # Тот, на кого подписан

    class Meta:
        unique_together = ('user', 'author')  # Нельзя подписаться дважды на одного и того же автора

    def __str__(self):
        return f"{self.user} follows {self.author}"  # Пример: "vasya follows olga"