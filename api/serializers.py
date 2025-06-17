from django.core.files.base import ContentFile
from rest_framework import serializers
from recipes.models import Ingredient, Recipe, RecipeIngredient, Tag
import base64
from users.models import User
from users.serializers import CustomUserSerializer

# Поле, которое умеет принимать изображение в base64 (удобно для API)
class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        # Если пришло изображение как строка base64 — обрабатываем вручную
        if isinstance(data, str) and data.startswith("data:image"):
            format, imgstr = data.split(";base64,")
            ext = format.split("/")[-1]
            data = ContentFile(base64.b64decode(imgstr), name=f"image.{ext}")
        return super().to_internal_value(data)


# Просто сериализатор ингредиента
class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ("id", "name", "measurement_unit")


# Ингредиент внутри рецепта (с количеством и его названием)
class IngredientInRecipeSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source="ingredient.id")  # Берём ID ингредиента
    name = serializers.CharField(source="ingredient.name", read_only=True)
    measurement_unit = serializers.CharField(
        source="ingredient.measurement_unit", read_only=True
    )

    class Meta:
        model = RecipeIngredient
        fields = ("id", "name", "measurement_unit", "amount")


# Сериализатор тега
class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ("id", "name", "color", "slug")


# Мини-версия рецепта — для отображения в избранном/корзине
class RecipeMinifiedSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = ("id", "name", "image", "cooking_time")

    def get_image(self, obj):
        request = self.context.get("request")
        return request.build_absolute_uri(obj.image.url) if obj.image else None


class RecipeListSerializer(serializers.ModelSerializer):
    author = CustomUserSerializer(read_only=True)  # Автор рецепта
    ingredients = IngredientInRecipeSerializer(
        source="recipeingredient_set", many=True, read_only=True
    )
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    image = serializers.SerializerMethodField()
    tags = TagSerializer(many=True, read_only=True)

    class Meta:
        model = Recipe
        fields = (
            "id",
            "author",
            "ingredients",
            "is_favorited",
            "is_in_shopping_cart",
            "name",
            "image",
            "text",
            "cooking_time",
            "tags",
        )

    def get_is_favorited(self, obj):
        request = self.context.get("request")
        return (
            request.user.is_authenticated
            and obj.favorite_set.filter(user=request.user).exists()
        )

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get("request")
        return (
            request.user.is_authenticated
            and obj.shoppingcart_set.filter(user=request.user).exists()
        )

    def get_image(self, obj):
        request = self.context.get("request")
        return request.build_absolute_uri(obj.image.url) if obj.image else None


# Сериализатор для создания/обновления рецепта
class RecipeCreateUpdateSerializer(serializers.ModelSerializer):
    ingredients = serializers.ListField(
        child=serializers.DictField(
            child=serializers.IntegerField(min_value=1)
        )
    )
    image = Base64ImageField()
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(), many=True
    )
    cooking_time = serializers.IntegerField(min_value=1)

    class Meta:
        model = Recipe
        fields = (
            "id",
            "ingredients",
            "image",
            "name",
            "text",
            "cooking_time",
            "tags",
        )

    def validate_ingredients(self, value):
        if not value:
            raise serializers.ValidationError(
                "Необходимо указать хотя бы один ингредиент."
            )
        ingredient_ids = [item["id"] for item in value]
        if len(ingredient_ids) != len(set(ingredient_ids)):
            raise serializers.ValidationError(
                "Ингредиенты не должны повторяться."
            )
        return value

    def create(self, validated_data):
        # При создании рецепта сохраняем теги и ингредиенты вручную
        ingredients_data = validated_data.pop("ingredients")
        tags = validated_data.pop("tags")
        recipe = Recipe.objects.create(
            author=self.context["request"].user, **validated_data
        )
        recipe.tags.set(tags)
        for item in ingredients_data:
            RecipeIngredient.objects.create(
                recipe=recipe,
                ingredient_id=item["id"],
                amount=item["amount"],
            )
        return recipe

    def update(self, instance, validated_data):
        # При обновлении рецепта — обновляем ингредиенты и теги
        ingredients_data = validated_data.pop("ingredients", None)
        tags = validated_data.pop("tags", None)
        if ingredients_data:
            instance.recipeingredient_set.all().delete()
            for item in ingredients_data:
                RecipeIngredient.objects.create(
                    recipe=instance,
                    ingredient_id=item["id"],
                    amount=item["amount"],
                )
        if tags:
            instance.tags.set(tags)
        return super().update(instance, validated_data)

    def to_representation(self, instance):
        # Чтобы вернуть результат в том же виде, как при чтении
        return RecipeListSerializer(instance, context=self.context).data