from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from recipes.models import Ingredient, Recipe, Tag, Favorite, ShoppingCart
from users.models import User, Subscription
from .serializers import (
    IngredientSerializer,
    RecipeListSerializer,
    RecipeCreateUpdateSerializer,
    TagSerializer,
    RecipeMinifiedSerializer,
    UserWithRecipesSerializer,
)
from .permissions import IsAuthorOrReadOnly
from .filters import RecipeFilter
from django.db.models import Sum
from django.contrib.auth import get_user_model
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from io import BytesIO
import shortuuid

User = get_user_model()


# Ингредиенты можно только смотреть (не добавлять/удалять)
class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_fields = ("name",)
    search_fields = ("^name",)


# Теги тоже только на чтение
class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer


# Полноценный viewset для рецептов: можно создавать, редактировать, удалять, читать
class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    permission_classes = (IsAuthorOrReadOnly,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def get_serializer_class(self):
        # Используем разный сериализатор для чтения и записи
        if self.action in ("create", "partial_update"):
            return RecipeCreateUpdateSerializer
        return RecipeListSerializer

    def get_queryset(self):
        # Добавляем фильтрацию по избранному и корзине — вручную, если юзер залогинен
        queryset = super().get_queryset()
        user = self.request.user
        if user.is_authenticated:
            is_favorited = self.request.query_params.get("is_favorited")
            if is_favorited == "1":
                queryset = queryset.filter(favorite_set__user=user)
            is_in_shopping_cart = self.request.query_params.get("is_in_shopping_cart")
            if is_in_shopping_cart == "1":
                queryset = queryset.filter(shoppingcart_set__user=user)
        return queryset


    # Добавить/удалить рецепт в избранное
    @action(detail=True, methods=["post", "delete"], permission_classes=[IsAuthenticated])
    def favorite(self, request, pk=None):
        recipe = get_object_or_404(Recipe, pk=pk)
        if request.method == "POST":
            if Favorite.objects.filter(user=request.user, recipe=recipe).exists():
                return Response(
                    {"error": "Рецепт уже в избранном"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            Favorite.objects.create(user=request.user, recipe=recipe)
            serializer = RecipeMinifiedSerializer(recipe, context={"request": request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        favorite = Favorite.objects.filter(user=request.user, recipe=recipe)
        if not favorite.exists():
            return Response(
                {"error": "Рецепта нет в избранном"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        favorite.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    # Добавить/удалить рецепт в список покупок
    @action(detail=True, methods=["post", "delete"], permission_classes=[IsAuthenticated])
    def shopping_cart(self, request, pk=None):
        recipe = get_object_or_404(Recipe, pk=pk)
        if request.method == "POST":
            if ShoppingCart.objects.filter(user=request.user, recipe=recipe).exists():
                return Response(
                    {"error": "Рецепт уже в списке покупок"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            ShoppingCart.objects.create(user=request.user, recipe=recipe)
            serializer = RecipeMinifiedSerializer(recipe, context={"request": request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        cart = ShoppingCart.objects.filter(user=request.user, recipe=recipe)
        if not cart.exists():
            return Response(
                {"error": "Рецепта нет в списке покупок"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        cart.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    # Заглушка под короткие ссылки (можно доработать при желании)
    @action(detail=True, methods=["get"])
    def get_link(self, request, pk=None):
        recipe = get_object_or_404(Recipe, pk=pk)
        short_id = shortuuid.uuid()[:8]
        short_link = f"http://localhost/s/{short_id}"
        return Response({"short-link": short_link})

    # Скачивание списка покупок в PDF
    @action(detail=False, methods=["get"], permission_classes=[IsAuthenticated])
    def download_shopping_cart(self, request):
        ingredients = (
            RecipeIngredient.objects.filter(
                recipe__shoppingcart__user=request.user
            )
            .values("ingredient__name", "ingredient__measurement_unit")
            .annotate(total_amount=Sum("amount"))
            .order_by("ingredient__name")
        )

        buffer = BytesIO()
        p = canvas.Canvas(buffer, pagesize=A4)
        p.setFont("Helvetica", 12)
        y = 800
        for item in ingredients:
            p.drawString(
                100,
                y,
                f"{item['ingredient__name']} - {item['total_amount']} {item['ingredient__measurement_unit']}",
            )
            y -= 20
        p.showPage()
        p.save()
        buffer.seek(0)
        response = HttpResponse(buffer, content_type="application/pdf")
        response["Content-Disposition"] = "attachment; filename=shopping_list.pdf"
        return response


# Управление пользователями (через API)
class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = CustomUserSerializer

    def get_permissions(self):
        # Разрешаем всем читать, а писать — только авторизованным
        if self.action in ("list", "retrieve"):
            return [AllowAny()]
        return super().get_permissions()

    # Возвращает данные о текущем пользователе
    @action(detail=False, methods=["get"], permission_classes=[IsAuthenticated])
    def me(self, request):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

    # Добавление/удаление аватара
    @action(detail=False, methods=["put", "delete"], permission_classes=[IsAuthenticated])
    def avatar(self, request):
        if request.method == "PUT":
            serializer = SetAvatarSerializer(
                request.user, data=request.data, context={"request": request}
            )
            if serializer.is_valid():
                serializer.save()
                return Response(
                    SetAvatarResponseSerializer(
                        request.user, context={"request": request}
                    ).data
                )
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        request.user.avatar.delete(save=True)
        return Response(status=status.HTTP_204_NO_CONTENT)

    # Список тех, на кого подписан пользователь
    @action(detail=False, methods=["get"], permission_classes=[IsAuthenticated])
    def subscriptions(self, request):
        queryset = User.objects.filter(subscribers__user=request.user)
        page = self.paginate_queryset(queryset)
        serializer = UserWithRecipesSerializer(
            page, many=True, context={"request": request}
        )
        return self.get_paginated_response(serializer.data)

    # Подписка/отписка на пользователя
    @action(detail=True, methods=["post", "delete"], permission_classes=[IsAuthenticated])
    def subscribe(self, request, pk=None):
        author = get_object_or_404(User, pk=pk)
        if author == request.user:
            return Response(
                {"error": "Нельзя подписаться на себя"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if request.method == "POST":
            if Subscription.objects.filter(user=request.user, author=author).exists():
                return Response(
                    {"error": "Вы уже подписаны"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            Subscription.objects.create(user=request.user, author=author)
            serializer = UserWithRecipesSerializer(
                author, context={"request": request}
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        subscription = Subscription.objects.filter(user=request.user, author=author)
        if not subscription.exists():
            return Response(
                {"error": "Вы не подписаны"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        subscription.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
