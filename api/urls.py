from django.urls import include, path
from rest_framework.routers import DefaultRouter
from .views import IngredientViewSet, RecipeViewSet, TagViewSet, UserViewSet

# Используем DRF Router, чтобы автоматически сгенерировать маршруты
router = DefaultRouter()
router.register('ingredients', IngredientViewSet)
router.register('tags', TagViewSet)
router.register('recipes', RecipeViewSet)
router.register('users', UserViewSet)

# Основные пути API + авторизация через Djoser
urlpatterns = [
    path('', include(router.urls)),  # /api/recipes/, /api/tags/ и т.п.
    path('auth/', include('djoser.urls')),  # регистрация, смена пароля и т.п.
    path('auth/', include('djoser.urls.authtoken')),  # вход по токену
]
