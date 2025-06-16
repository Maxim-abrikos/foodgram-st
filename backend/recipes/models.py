from django.core.validators import MinValueValidator
from django.db import models
from users.models import User

# Ингредиент — например, "Молоко", "Сахар"
class Ingredient(models.Model):
    name = models.CharField(max_length=128, unique=True)  # Название ингредиента
    measurement_unit = models.CharField(max_length=64)  # Единица измерения (г, мл, шт)

    class Meta:
        ordering = ['name']  # Сортировка по имени

    def __str__(self):
        return f"{self.name} ({self.measurement_unit})"

# Тег для рецепта, например: "Завтрак", "Вегетарианское"
class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True)
    color = models.CharField(max_length=7)  # HEX-цвет, например "#FF5733"
    slug = models.SlugField(max_length=50, unique=True)  # Уникальный короткий идентификатор

    def __str__(self):
        return self.name

# Основная модель рецепта
class Recipe(models.Model):
    author = models.ForeignKey(User, related_name='recipes', on_delete=models.CASCADE)  # Кто создал рецепт
    name = models.CharField(max_length=256)  # Название рецепта
    image = models.ImageField(upload_to='recipes/images/')  # Картинка рецепта
    text = models.TextField()  # Описание, способ приготовления
    ingredients = models.ManyToManyField(Ingredient, through='RecipeIngredient')  # Ингредиенты через связь
    tags = models.ManyToManyField(Tag)  # Теги — можно выбрать несколько
    cooking_time = models.PositiveIntegerField(validators=[MinValueValidator(1)])  # Время готовки в минутах

    class Meta:
        ordering = ['-id']  # Сортировка: сначала новые рецепты

    def __str__(self):
        return self.name

# Связующая таблица "ингредиент в рецепте" с указанием количества
class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE)
    amount = models.PositiveIntegerField(validators=[MinValueValidator(1)])  # Сколько нужно (не менее 1)

    class Meta:
        unique_together = ('recipe', 'ingredient')  # Нельзя добавить один и тот же ингредиент дважды

# Модель "Избранное" — пользователь добавил рецепт в любимые
class Favorite(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('user', 'recipe')  # Один пользователь не может добавить один рецепт в избранное дважды

# Модель "Список покупок" — пользователь добавил рецепт в корзину
class ShoppingCart(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('user', 'recipe')  # Один и тот же рецепт не может быть дважды в корзине
