from django.core.validators import MinValueValidator
from django.db import models
from users.models import User

class Ingredient(models.Model):
    name = models.CharField(max_length=128, unique=True)
    measurement_unit = models.CharField(max_length=64)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.measurement_unit})"

class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True)
    color = models.CharField(max_length=7)  # HEX-код
    slug = models.SlugField(max_length=50, unique=True)

    def __str__(self):
        return self.name

class Recipe(models.Model):
    author = models.ForeignKey(User, related_name='recipes', on_delete=models.CASCADE)
    name = models.CharField(max_length=256)
    image = models.ImageField(upload_to='recipes/images/')
    text = models.TextField()
    ingredients = models.ManyToManyField(Ingredient, through='RecipeIngredient')
    tags = models.ManyToManyField(Tag)
    cooking_time = models.PositiveIntegerField(validators=[MinValueValidator(1)])

    class Meta:
        ordering = ['-id']

    def __str__(self):
        return self.name

class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE)
    amount = models.PositiveIntegerField(validators=[MinValueValidator(1)])

    class Meta:
        unique_together = ('recipe', 'ingredient')

class Favorite(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('user', 'recipe')

class ShoppingCart(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('user', 'recipe')