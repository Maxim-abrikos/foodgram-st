from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _
from .models import (
    CookingRecipe, ProductComponent, RecipeComponent, 
    FavoriteRecipe, ShoppingCart, User, UserSubscription
)



class BaseHasRelatedFilter(admin.SimpleListFilter):
    title = ''
    parameter_name = ''
    lookups_choices = ()
    related_field = ''

    def lookups(self, request, model_admin):
        return self.lookups_choices

    def queryset(self, request, queryset):
        if self.value() == 'yes':
            return queryset.filter(**{f'{self.related_field}__isnull': False}).distinct()
        if self.value() == 'no':
            return queryset.filter(**{f'{self.related_field}__isnull': True}).distinct()


class HasRecipesFilter(BaseHasRelatedFilter):
    title = _('наличие рецептов')
    parameter_name = 'has_recipes'
    lookups_choices = (
        ('yes', _('Есть рецепты')),
        ('no', _('Нет рецептов')),
    )
    related_field = 'recipes'


class HasSubscriptionsFilter(BaseHasRelatedFilter):
    title = _('наличие подписок')
    parameter_name = 'has_subscriptions'
    lookups_choices = (
        ('yes', _('Есть подписки')),
        ('no', _('Нет подписок')),
    )
    related_field = 'following'


class HasSubscribersFilter(BaseHasRelatedFilter):
    title = _('наличие подписчиков')
    parameter_name = 'has_subscribers'
    lookups_choices = (
        ('yes', _('Есть подписчики')),
        ('no', _('Нет подписчиков')),
    )
    related_field = 'followers'


@admin.register(User)
class FoodgramUserAdmin(UserAdmin):
    
    list_display = (
        'id', 'username', 'get_full_name', 'email', 
        'get_avatar', 'recipes_count', 'subscribers_count', 
        'subscriptions_count'
    )
    search_fields = ('email', 'username', 'first_name', 'last_name')
    list_filter = (
        'is_staff', 'is_active', 'date_joined', 
        HasRecipesFilter, HasSubscriptionsFilter, HasSubscribersFilter
    )
    ordering = ('username',)
    readonly_fields = (
        'date_joined', 'last_login', 'recipes_count', 
        'subscribers_count', 'subscriptions_count', 'get_avatar'
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related(
            'recipes', 'following', 'followers'
        )
    
    @admin.display(description=_('ФИО'), ordering='first_name')
    def get_full_name(self, user):
        """ФИО пользователя"""
        return f"{user.first_name} {user.last_name}".strip()
    
    @admin.display(description=_('рецептов'), ordering='recipes')
    def recipes_count(self, user):
        """Количество рецептов пользователя"""
        return user.recipes.count()
    
    @admin.display(description=_('Подписчиков'), ordering='followers')
    def subscribers_count(self, user):
        """Количество подписчиков"""
        return user.followers.count()
    
    @admin.display(description=_('Подписок'), ordering='following')
    def subscriptions_count(self, user):
        """Количество подписок"""
        return user.following.count()
    
    @admin.display(description=_('Аватар'))
    def get_avatar(self, user):
        """Отображение аватара в админке"""
        if user.avatar:
            return mark_safe(
                f'<img src="{user.avatar.url}" width="50" height="50" style="border-radius: 50%;" />'
            )
        return _('Нет аватара')


@admin.register(UserSubscription)
class UserSubscriptionAdmin(admin.ModelAdmin):
    
    list_display = (
        'subscriber', 'target_user', 'get_subscriber_email', 
        'get_target_email', 'get_subscription_info'
    )
    search_fields = (
        'subscriber__email', 'target_user__email', 
        'subscriber__username', 'target_user__username'
    )
    list_filter = ('subscriber', 'target_user')
    ordering = ('subscriber',)
    
    @admin.display(description=_('Email подписчика'), ordering='subscriber__email')
    def get_subscriber_email(self, obj):
        """Email подписчика"""
        return obj.subscriber.email
    
    @admin.display(description=_('Email автора'), ordering='target_user__email')
    def get_target_email(self, obj):
        """Email целевого пользователя"""
        return obj.target_user.email
    
    @admin.display(description=_('Рецептов у автора'))
    def get_subscription_info(self, obj):
        """Дополнительная информация о подписке"""
        target_recipes = obj.target_user.authored_recipes.count()
        return f"{target_recipes} {_('рецептов')}"

class HasInRecipesFilter(BaseHasRelatedFilter):
    title = _('наличие в рецептах')
    parameter_name = 'has_in_recipes'
    lookups_choices = (
        ('yes', _('Есть в рецептах')),
        ('no', _('Нет в рецептах')),
    )
    related_field = 'recipe_components'

@admin.register(ProductComponent)
class ProductComponentAdmin(admin.ModelAdmin):
    
    list_display = ('title', 'unit_type', 'recipe_count')
    search_fields = ('title', 'unit_type')
    list_filter = ('unit_type', HasInRecipesFilter)
    ordering = ('title',)
    
    @admin.display(description=_('Количество рецептов'))
    def recipe_count(self, obj):
        """Количество рецептов с этим ингредиентом"""
        return obj.recipe_components.count()


@admin.register(CookingRecipe)
class CookingRecipeAdmin(admin.ModelAdmin):
    
    list_display = (
        'id', 'title', 'cook_duration', 'creator', 
        'favorites_count', 'get_ingredients', 'get_image'
    )
    search_fields = ('title', 'creator__email', 'creator__username')
    list_filter = ('creator', 'date_created')
    ordering = ('-date_created',)
    readonly_fields = ('date_created', 'get_ingredients', 'get_image', 'favorites_count')
    
    @admin.display(description=_('Продукты'))
    def get_ingredients(self, obj):
        """Отображение продуктов в админке"""
        return mark_safe("<br>".join(
            f"{ingredient.component.title} - {ingredient.quantity} {ingredient.component.unit_type}"
            for ingredient in obj.recipe_components.select_related('component')
        ))
    
    @admin.display(description=_('Изображение'))
    def get_image(self, obj):
        """Отображение картинки в админке"""
        if obj.picture:
            return mark_safe(
                f'<img src="{obj.picture.url}" width="50" height="50" style="border-radius: 5px;" />'
            )
        return _('Нет изображения')
    
    @admin.display(description=_('В избранном'), ordering='favorite_recipes')
    def favorites_count(self, obj):
        """Количество добавлений в избранное"""
        return obj.favorite_recipes.count()


@admin.register(RecipeComponent)
class RecipeComponentAdmin(admin.ModelAdmin):
    
    list_display = ('recipe', 'component', 'quantity')
    search_fields = ('recipe__title', 'component__title')
    list_filter = ('recipe', 'component')
    ordering = ('recipe',)


@admin.register(FavoriteRecipe)
class FavoriteRecipeAdmin(admin.ModelAdmin):
    
    list_display = ('user', 'recipe', 'get_recipe_title')
    search_fields = ('user__email', 'user__username', 'recipe__title')
    list_filter = ('recipe__creator', 'recipe__date_created')
    ordering = ('-id',)
    
    @admin.display(description=_('Название рецепта'), ordering='recipe__title')
    def get_recipe_title(self, obj):
        """Название рецепта для удобства"""
        return obj.recipe.title


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    
    list_display = ('user', 'recipe', 'get_recipe_title', 'get_recipe_author')
    search_fields = ('user__email', 'user__username', 'recipe__title')
    list_filter = ('recipe__creator', 'recipe__date_created')
    ordering = ('-id',)
    
    @admin.display(description=_('Название рецепта'), ordering='recipe__title')
    def get_recipe_title(self, obj):
        """Название рецепта для удобства"""
        return obj.recipe.title
    
    @admin.display(description=_('Автор рецепта'), ordering='recipe__creator')
    def get_recipe_author(self, obj):
        """Автор рецепта для удобства"""
        return obj.recipe.creator.get_full_name() or obj.recipe.creator.username


class CustomAdminSite(admin.AdminSite):
    def index(self, request, extra_context=None):
        extra_context = extra_context or {}
        
  
        recipe_stats = {
            'total_recipes': CookingRecipe.objects.count(),
            'total_users': User.objects.count(),
            'total_ingredients': ProductComponent.objects.count(),
            'recipes_in_favorites': FavoriteRecipe.objects.values('recipe').distinct().count(),
            'recipes_in_carts': ShoppingCart.objects.values('recipe').distinct().count(),
        }
        
        extra_context['recipe_stats'] = recipe_stats
        return super().index(request, extra_context)


admin.site.site_header = _('Администрирование Foodgram')
admin.site.site_title = _('Foodgram Admin')
admin.site.index_title = _('Добро пожаловать в админ-панель Foodgram')