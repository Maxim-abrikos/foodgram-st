from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, RegexValidator
from django.db import models
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):
    
    email = models.EmailField(_('Электронная почта'), unique=True, max_length=254)
    username = models.CharField(
        _('Псевдоним пользователя'),
        max_length=150,
        unique=True,
        validators=[
            RegexValidator(
                regex=r'^[\w.@+-]+\Z'
            )
        ]
    )
    first_name = models.CharField(_('Имя'), max_length=150)
    last_name = models.CharField(_('Фамилия'), max_length=150)
    avatar = models.ImageField(
        _('Аватар пользователя'),
        upload_to='users/avatars',
        null=True,
        blank=True
    )
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    class Meta(AbstractUser.Meta):
        ordering = ('username',)
        verbose_name = _('Пользователь')
        verbose_name_plural = _('Пользователи')


class UserSubscription(models.Model):
    
    subscriber = models.ForeignKey(
        User,
        verbose_name=_('Подписчик'),
        related_name='subscriptions',
        on_delete=models.CASCADE
    )
    target_user = models.ForeignKey(
        User,
        verbose_name=_('Подписки авторов'),
        related_name='authors',
        on_delete=models.CASCADE
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['subscriber', 'target_user'],
                name='unique_user_subscription'
            )
        ]
        verbose_name = _('Подписка')
        verbose_name_plural = _('Подписки')

    def __str__(self):
        return f"{self.subscriber} подписан на {self.target_user}"


class ProductComponent(models.Model):
    
    title = models.CharField(_('Наименование'), max_length=128)
    unit_type = models.CharField(_('Единица измерения'), max_length=64)

    class Meta:
        ordering = ('title',)
        verbose_name = _('Продукт')
        verbose_name_plural = _('Продукты')

    def __str__(self):
        return f"{self.title} ({self.unit_type})"


class CookingRecipe(models.Model):
    
    title = models.CharField(_('Название рецепта'), max_length=256)
    description = models.TextField(_('Описание приготовления'))
    cook_duration = models.PositiveSmallIntegerField(
        _('Время приготовления (мин)'),
        validators=[
            MinValueValidator(1)
        ]
    )
    picture = models.ImageField(_('Изображение блюда'), upload_to='recipes/images')
    creator = models.ForeignKey(
        User,
        verbose_name=_('Автор рецепта'),
        related_name='recipes',
        on_delete=models.CASCADE
    )
    components = models.ManyToManyField(
        ProductComponent,
        through='RecipeComponent',
        related_name='recipes',
        verbose_name=_('Список продуктов'),
        through_fields=('recipe', 'component')
    )
    date_created = models.DateTimeField(_('Дата создания'), auto_now_add=True)

    class Meta:
        ordering = ('-date_created',)
        verbose_name = _('Рецепт')
        verbose_name_plural = _('Рецепты')

    def __str__(self):
        return self.title

class BaseUserRecipeRelation(models.Model):
    
    user = models.ForeignKey(
        User,
        verbose_name=_('Пользователь'),
        on_delete=models.CASCADE
    )
    recipe = models.ForeignKey(
        CookingRecipe,
        verbose_name=_('Рецепт'),
        on_delete=models.CASCADE
    )

    class Meta:
        abstract = True
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='%(class)s_unique_user_recipe'
            )
        ]

    def __str__(self):
        return f"{self.recipe} - {self.user}"


class RecipeComponent(models.Model):
    
    recipe = models.ForeignKey(
        CookingRecipe,
        verbose_name=_('Рецепт'),
        on_delete=models.CASCADE
    )
    component = models.ForeignKey(
        ProductComponent,
        verbose_name=_('Продукт'),
        related_name='recipe_components',
        on_delete=models.CASCADE
    )
    quantity = models.PositiveIntegerField(
        _('Количество'),
        validators=[
            MinValueValidator(1)
        ]
    )

    class Meta:
        ordering = ('recipe', 'component')
        verbose_name = _('Продукт в рецепте')
        verbose_name_plural = _('Продукты в рецептах')
        constraints = [
            models.UniqueConstraint(
                fields=['recipe', 'component'],
                name='unique_recipe_component'
            )
        ]
        default_related_name = 'recipe_components'

    def __str__(self):
        return f"{self.component} для {self.recipe}"


class ShoppingCart(BaseUserRecipeRelation):
    
    class Meta(BaseUserRecipeRelation.Meta):
        verbose_name = _('Элемент корзины')
        verbose_name_plural = _('Корзина покупок')
        default_related_name = 'shopping_items'


class FavoriteRecipe(BaseUserRecipeRelation):
    
    class Meta(BaseUserRecipeRelation.Meta):
        verbose_name = _('Избранный рецепт')
        verbose_name_plural = _('Избранные рецепты')
        default_related_name = 'favorite_recipes'
