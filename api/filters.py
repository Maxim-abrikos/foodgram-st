from django_filters.rest_framework import FilterSet, NumberFilter, BooleanFilter
from recipes.models import Recipe

class RecipeFilter(FilterSet):
    is_favorited = BooleanFilter(method="filter_is_favorited")  # Фильтр по избранному
    is_in_shopping_cart = BooleanFilter(method="filter_is_in_shopping_cart")  # Фильтр по корзине
    author = NumberFilter(field_name="author__id")  # Фильтр по автору
    tags = NumberFilter(field_name="tags__id", lookup_expr="in")  # Фильтр по тегам

    def filter_is_favorited(self, queryset, name, value):
        if value and self.request.user.is_authenticated:
            return queryset.filter(favorite_set__user=self.request.user)
        return queryset

    def filter_is_in_shopping_cart(self, queryset, name, value):
        if value and self.request.user.is_authenticated:
            return queryset.filter(shoppingcart_set__user=self.request.user)
        return queryset

    class Meta:
        model = Recipe
        fields = ["is_favorited", "is_in_shopping_cart", "author", "tags"]
