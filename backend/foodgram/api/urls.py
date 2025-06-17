from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    ProductComponentViewSet,
    CookingRecipeViewSet,
    UserViewSet,
)

router = DefaultRouter()
router.register(r'recipes', CookingRecipeViewSet, basename='recipes')
router.register(r'ingredients', ProductComponentViewSet,  basename='ingredients')
router.register(r'users', UserViewSet, basename='users')

urlpatterns = [
    path('', include(router.urls)),
    path('auth/', include('djoser.urls.authtoken')),
]