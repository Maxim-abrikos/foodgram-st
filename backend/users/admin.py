from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Subscription

# Регистрируем модель User в админке, используя готовый UserAdmin
@admin.register(User)
class UserAdmin(UserAdmin):
    list_display = ("username", "email", "first_name", "last_name")  # Какие поля показать в списке
    search_fields = ("email", "username")  # По каким полям можно искать


# Регистрируем модель подписок в админке
@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ("user", "author")  # Показываем, кто на кого подписан