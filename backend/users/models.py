from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    email = models.EmailField(max_length=254, unique=True)
    username = models.CharField(max_length=150, unique=True)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    avatar = models.ImageField(upload_to='users/avatars/', null=True, blank=True)

    class Meta:
        ordering = ['username']

    def __str__(self):
        return self.username

class Subscription(models.Model):
    user = models.ForeignKey(User, related_name='subscriptions', on_delete=models.CASCADE)
    author = models.ForeignKey(User, related_name='subscribers', on_delete=models.CASCADE)

    class Meta:
        unique_together = ('user', 'author')

    def __str__(self):
        return f"{self.user} follows {self.author}"