from django.contrib import admin
from .models import Ingredient, Recipe, Tag, RecipeIngredient, Favorite, ShoppingCart

# Отображение ингредиентов в админке
@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ("name", "measurement_unit")  # Показываем название и единицу измерения
    search_fields = ("name",)  # Можно искать по названию


# Отображение рецептов
@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ("name", "author", "favorites_count")  # Название рецепта, автор, сколько добавили в избранное
    search_fields = ("name", "author__username")  # Поиск по названию и имени автора
    list_filter = ("tags",)  # Фильтр по тегам

    def favorites_count(self, obj):
        return obj.favorite_set.count()  # Сколько пользователей добавили рецепт в избранное

    favorites_count.short_description = "Добавлений в избранное"  # Подпись в колонке


# Отображение тегов
@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ("name", "color", "slug")  # Название, цвет и "slug"-идентификатор


# Показываем, какие ингредиенты в каких рецептах и в каком количестве
@admin.register(RecipeIngredient)
class RecipeIngredientAdmin(admin.ModelAdmin):
    list_display = ("recipe", "ingredient", "amount")


# Отображение избранных рецептов
@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ("user", "recipe")  # Кто и что добавил в избранное


# Отображение корзины покупок
@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    list_display = ("user", "recipe")  # Кто и что добавил в список покупок
