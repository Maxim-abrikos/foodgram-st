from django.contrib.auth import get_user_model
from rest_framework import serializers
from recipes.models import Recipe
from .models import Subscription

User = get_user_model()  # Получаем кастомную модель пользователя

# Сериализатор для отображения пользователя с доп. флагом "подписан ли я на него"
class CustomUserSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField()  # Это поле рассчитывается вручную

    class Meta:
        model = User
        fields = ('email', 'id', 'username', 'first_name', 'last_name', 'is_subscribed', 'avatar')

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        # Если пользователь не залогинен, он ни на кого не подписан
        if not request or not request.user.is_authenticated:
            return False
        # Проверяем, есть ли подписка текущего юзера на этого obj'а
        return Subscription.objects.filter(user=request.user, author=obj).exists()

# Сериализатор для регистрации нового пользователя
class CustomUserCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('email', 'id', 'username', 'first_name', 'last_name', 'password')
        extra_kwargs = {'password': {'write_only': True}}  # Пароль не возвращаем клиенту

    def create(self, validated_data):
        # Создание пользователя через встроенный метод Django
        user = User.objects.create_user(**validated_data)
        return user

# Сериализатор для отображения пользователя + его рецептов
class UserWithRecipesSerializer(CustomUserSerializer):
    recipes = serializers.SerializerMethodField()  # Добавим список рецептов пользователя
    recipes_count = serializers.SerializerMethodField()  # Кол-во рецептов

    class Meta(CustomUserSerializer.Meta):
        fields = CustomUserSerializer.Meta.fields + ('recipes', 'recipes_count')

    def get_recipes(self, obj):
        from api.serializers import RecipeMinifiedSerializer
        request = self.context.get('request')
        limit = request.query_params.get('recipes_limit', None)
        recipes = obj.recipes.all()
        if limit:
            recipes = recipes[:int(limit)]  # Обрезаем по лимиту, если он указан
        return RecipeMinifiedSerializer(recipes, many=True, context=self.context).data

    def get_recipes_count(self, obj):
        return obj.recipes.count()  # Просто считаем, сколько у автора рецептов

# Сериализатор для обновления аватара
class SetAvatarSerializer(serializers.ModelSerializer):
    avatar = serializers.ImageField()  # Ожидаем поле "avatar" с картинкой

    class Meta:
        model = User
        fields = ('avatar',)

# Сериализатор для ответа при получении аватара — возвращает полную ссылку
class SetAvatarResponseSerializer(serializers.ModelSerializer):
    avatar = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('avatar',)

    def get_avatar(self, obj):
        request = self.context.get('request')
        # Генерируем абсолютную ссылку на файл, если он есть
        return request.build_absolute_uri(obj.avatar.url) if obj.avatar else None
