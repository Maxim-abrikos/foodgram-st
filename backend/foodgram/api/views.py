from datetime import datetime
from django.db.models import Sum
from django.forms import ValidationError
from django.http import FileResponse
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from rest_framework import filters, viewsets, permissions, status
from rest_framework.permissions import AllowAny
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet as DjoserUserViewSet

from recipes.models import CookingRecipe, ProductComponent, ShoppingCart, RecipeComponent, FavoriteRecipe
from recipes.models import UserSubscription, User
from .serializers import (
    ProductSerializer, CookingRecipeSerializer, CookingRecipeShortSerializer, 
    UserSubscriptionSerializer, UserSerializer
)
from .permissions import CreatorOrReadOnly
from .filters import CookingRecipeFilter

UserModel = get_user_model()


class ProductComponentViewSet(viewsets.ReadOnlyModelViewSet):
    
    queryset = ProductComponent.objects.all()
    serializer_class = ProductSerializer
    pagination_class = None
    permission_classes = [AllowAny]
    filter_backends = (DjangoFilterBackend, filters.SearchFilter)
    filterset_fields = ('title',)
    search_fields = ('^title',)

    def get_queryset(self):
        search_term = self.request.query_params.get('title')
        if search_term:
            return self.queryset.filter(title__istartswith=search_term)
        return self.queryset


class CookingRecipeViewSet(viewsets.ModelViewSet):
    
    serializer_class = CookingRecipeSerializer
    pagination_class = LimitOffsetPagination
    permission_classes = (CreatorOrReadOnly,)
    filter_backends = (DjangoFilterBackend, filters.SearchFilter)
    search_fields = ('title',)
    filterset_class = CookingRecipeFilter

    def get_queryset(self):
        return (
            CookingRecipe.objects
            .select_related('creator')
            .prefetch_related('recipe_components__component', 'favorite_recipes', 'shopping_items')
        )

    def perform_create(self, serializer):
        serializer.save(creator=self.request.user)

    def _handle_recipe_relation(self, request, pk, model_class):
        
        recipe = get_object_or_404(CookingRecipe, pk=pk)
        user = request.user
        verbose = model_class._meta.verbose_name
        if request.method == 'POST':
            _, created = model_class.objects.get_or_create(user=user, recipe=recipe)
            if not created:
                raise ValidationError({
                    'detail': f'{verbose.capitalize()} для рецепта "{recipe.title}" уже существует.'
                })
            serializer = CookingRecipeShortSerializer(recipe)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        get_object_or_404(model_class, user=user, recipe=recipe).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True, 
        methods=['post', 'delete'], 
        url_path='shopping_cart',  
        permission_classes=[permissions.IsAuthenticated]
    )
    def handle_shopping_cart(self, request, pk=None):
        return self._handle_recipe_relation(request, pk, ShoppingCart)

    @action(
        detail=False, 
        methods=['get'], 
        url_path='download-shopping-list',
        permission_classes=[permissions.IsAuthenticated]
    )
    def download_shopping_list(self, request):
        user = request.user
        shopping_list = (
            RecipeComponent.objects
            .filter(recipe__shopping_items__user=user) 
            .values('component__title', 'component__unit_type')
            .annotate(total_quantity=Sum('quantity'))
            .order_by('component__title')
        )
        recipes_in_cart = (
            CookingRecipe.objects
            .filter(shopping_items__user=user)  
            .select_related('creator')
            .values('title', 'creator__username', 'creator__first_name', 'creator__last_name')
        )
        content = '\n'.join([
            f'Список покупок на {datetime.now().strftime("%d.%m.%Y")}',
            '',
            'ПРОДУКТЫ:',
            *[
                f'{index}. {item["component__title"].capitalize()} - '
                f'{item["total_quantity"]} {item["component__unit_type"]}'
                for index, item in enumerate(shopping_list, 1)
            ],
            '',
            'РЕЦЕПТЫ:',
            *[
                f'• {recipe["title"]} (автор: '
                f'{recipe["creator__first_name"]} {recipe["creator__last_name"]} '
                f'@{recipe["creator__username"]})'
                for recipe in recipes_in_cart
            ],
        ])
        return FileResponse(
            content,
            as_attachment=True,
            filename='shopping_list.txt',
            content_type='text/plain'
        )

    @action(
        detail=True, 
        methods=['post', 'delete'], 
        url_path='favorite',
        permission_classes=[permissions.IsAuthenticated]
    )
    def handle_favorites(self, request, pk=None):
        return self._handle_recipe_relation(request, pk, FavoriteRecipe)

    @action(
        detail=True, 
        methods=['get'], 
        url_path='get-link',
        permission_classes=[permissions.IsAuthenticatedOrReadOnly]
    )
    def get_link(self, request, pk=None):

        recipe_exists = CookingRecipe.objects.filter(pk=pk).exists()
        if not recipe_exists:
            return Response({'error': f'Рецепт с id={pk} не найден'}, status=status.HTTP_404_NOT_FOUND)

        short_link = request.build_absolute_uri(reverse('recipes:short-link', kwargs={'pk': pk}))
        return Response({'short-link': short_link})


class UserViewSet(DjoserUserViewSet):
    
    queryset = User.objects.all()
    serializer_class = UserSerializer
    pagination_class = LimitOffsetPagination
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    @action(
        detail=False, 
        methods=['get'], 
        url_path='me', 
        permission_classes=[permissions.IsAuthenticated]
    )
    def me(self, request, *args, **kwargs):
        """Получить текущего пользователя"""
        return super().me(request, *args, **kwargs)

    @action(
        detail=False, 
        methods=['put', 'delete'], 
        url_path='me/avatar', 
        permission_classes=[permissions.IsAuthenticated]
    )
    def avatar(self, request):
        """Управление аватаром пользователя"""
        user_instance = request.user
        
        if request.method == 'PUT':
            serializer = self.get_serializer(
                user_instance, 
                data=request.data, 
                partial=True
            )
            serializer.is_valid(raise_exception=True)
            
            avatar_data = request.data.get('avatar')
            if not avatar_data:
                return Response(
                    {'avatar': 'Поле avatar обязательно для заполнения!'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            if user_instance.avatar:
                user_instance.avatar.delete()
            
            serializer.save()
            return Response(
                {'avatar': serializer.data['avatar']}, 
                status=status.HTTP_200_OK
            )
        
        if not user_instance.avatar:
            return Response(
                {'detail': 'У пользователя нет аватара'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user_instance.avatar.delete()
        user_instance.save()
        return Response(
            {'message': 'Аватар успешно удален'}, 
            status=status.HTTP_204_NO_CONTENT
        )

    @action(
        detail=False, 
        methods=['get'], 
        url_path='subscriptions',
        permission_classes=[permissions.IsAuthenticated]
    )
    def subscriptions(self, request):
        """Получить список подписок пользователя"""
        subscribed_users = User.objects.filter(
            authors__subscriber=request.user 
        ).prefetch_related('recipes')
        
        page = self.paginate_queryset(subscribed_users)
        serializer = UserSubscriptionSerializer(page, many=True, context={'request': request})
        return self.get_paginated_response(serializer.data)
        
    @action(
        detail=True, 
        methods=['post', 'delete'], 
        url_path='subscribe',
        permission_classes=[permissions.IsAuthenticated]
    )
    def subscribe(self, request, pk=None):
        """Подписаться/отписаться от пользователя"""
        target_user = get_object_or_404(User, pk=pk)
        
        if request.method == 'POST':
            if target_user == request.user:
                return Response(
                    {'detail': 'Нельзя подписаться на самого себя'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            _, created = UserSubscription.objects.get_or_create(
                subscriber=request.user, 
                target_user=target_user
            )
            if not created:
                return Response(
                    {'detail': f'Вы уже подписаны на пользователя {target_user.username}'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            serializer = UserSubscriptionSerializer(target_user, context={'request': request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        subscription = get_object_or_404(
            UserSubscription, 
            subscriber=request.user, 
            target_user=target_user
        )
        subscription.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
