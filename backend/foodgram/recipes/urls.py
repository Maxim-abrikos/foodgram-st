from django.urls import path
from . import views


urlpatterns = [
    path('<int:recipe_id>/', views.redirect_to_recipe, name='short-link'),
]