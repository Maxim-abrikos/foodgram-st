from rest_framework import serializers
from drf_extra_fields.fields import Base64ImageField
from djoser.serializers import UserSerializer as DjoserUserSerializer

from recipes.models import CookingRecipe, ProductComponent, RecipeComponent, FavoriteRecipe, ShoppingCart
from recipes.models import User, UserSubscription


class UserSerializer(DjoserUserSerializer):

    is_subscribed = serializers.SerializerMethodField(read_only=True)
    avatar = Base64ImageField(required=False, allow_null=True)

    class Meta(DjoserUserSerializer.Meta):
        model = User
        fields = DjoserUserSerializer.Meta.fields + (
            'is_subscribed', 'avatar'
        )
        read_only_fields = fields

    def get_is_subscribed(self, user):
        request = self.context.get('request')
        return (
            request and request.user.is_authenticated and 
            user != request.user and
            UserSubscription.objects.filter(
                subscriber=request.user, 
                target_user=user
            ).exists()
        )


class ProductSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = ProductComponent
        fields = ('id', 'title', 'unit_type')


class ComponentInputSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(queryset=ProductComponent.objects.all())
    quantity = serializers.IntegerField(min_value=1)
    class Meta:
        model = RecipeComponent
        fields = ('id', 'quantity')


class ComponentOutputSerializer(serializers.ModelSerializer):
    
    id = serializers.IntegerField(source='component.id', read_only=True)
    title = serializers.CharField(source='component.title', read_only=True)
    unit_type = serializers.CharField(source='component.unit_type', read_only=True)

    class Meta:
        model = RecipeComponent
        fields = ('id', 'title', 'unit_type', 'quantity')
        read_only_fields = fields


class CookingRecipeSerializer(serializers.ModelSerializer):
    
    creator = UserSerializer(read_only=True)
    picture = Base64ImageField(required=True)
    components = ComponentInputSerializer(many=True, write_only=True)
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    cook_duration = serializers.IntegerField(min_value=1)

    class Meta:
        model = CookingRecipe
        fields = (
            'id', 'creator', 'title', 'description', 'picture', 'cook_duration',
            'components', 'is_favorited', 'is_in_shopping_cart'
        )
        read_only_fields = ('creator', 'is_favorited', 'is_in_shopping_cart')

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['components'] = ComponentOutputSerializer(
            instance.recipe_components.select_related('component'), many=True
        ).data
        return representation

    def get_is_favorited(self, obj):
        user = self.context.get('request').user
        return (
            user and user.is_authenticated and 
            FavoriteRecipe.objects.filter(user=user, recipe=obj).exists()
        )

    def get_is_in_shopping_cart(self, obj):
        user = self.context.get('request').user
        return (
            user and user.is_authenticated and 
            ShoppingCart.objects.filter(user=user, recipe=obj).exists()
        )

    def validate_components(self, components_list):
        if not isinstance(components_list, list) or not components_list:
            raise serializers.ValidationError('Список продуктов не может быть пустым!')
        
        component_ids = [
            item['id'].id if hasattr(item['id'], 'id') else item['id'] 
            for item in components_list
        ]
        
        if len(component_ids) != len(set(component_ids)):
            raise serializers.ValidationError('Продукты не должны повторяться!')
        
        return components_list

    def create(self, validated_data):
        components = validated_data.pop('components')
        recipe = super().create(validated_data)
        self._create_recipe_components(recipe, components)
        return recipe

    def update(self, instance, validated_data):
        components = validated_data.pop('components')
        instance.recipe_components.all().delete()
        self._create_recipe_components(instance, components)
        return super().update(instance, validated_data)
        

    def _create_recipe_components(self, recipe, components):
        RecipeComponent.objects.bulk_create([
            RecipeComponent(
                recipe=recipe,
                component=component_data['id'],
                quantity=component_data['quantity']
            )
            for component_data in components
        ])


class CookingRecipeShortSerializer(serializers.ModelSerializer):
    

    class Meta:
        model = CookingRecipe
        fields = ('id', 'title', 'picture', 'cook_duration')
        read_only_fields = fields


class UserSubscriptionSerializer(UserSerializer):
    
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.IntegerField(
        source='recipes.count', read_only=True
    )

    class Meta(UserSerializer.Meta):
        fields = [*UserSerializer.Meta.fields, 'recipes', 'recipes_count']
        read_only_fields = fields

    def get_recipes(self, user):
        recipes_queryset = user.recipes.all()
        recipes_limit = self.context['request'].query_params.get('recipes_limit')
        
        if recipes_limit:
            recipes_queryset = recipes_queryset[:int(recipes_limit)]
        
        return CookingRecipeShortSerializer(
            recipes_queryset, 
            many=True, 
            context=self.context
        ).data
