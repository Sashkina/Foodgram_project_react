import base64

from django.core.files.base import ContentFile
from django.db import transaction
from djoser.serializers import UserSerializer
from recipes.models import (Favorite, Ingredient, IngredientRecipe, Recipe,
                            ShoppingCart, Subscribe, Tag)
from rest_framework import serializers
from rest_framework.relations import PrimaryKeyRelatedField, SlugRelatedField
from users.models import CustomUser


class Base64ImageField(serializers.ImageField):
    """Кастомный тип поля для image field в модели Recipe"""
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)

        return super().to_internal_value(data)


class CustomUserSerializer(UserSerializer):
    """Сериализатор для модели CustomUser"""
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = CustomUser
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed'
        )

    def get_is_subscribed(self, obj):
        try:
            request = self.context.get('request')
            user = request.user
            return Subscribe.objects.filter(following=obj, user=user).exists()
        except Exception:
            return False


class PasswordSerializer(serializers.Serializer):
    """Сериализатор для смены пароля (set_password)"""
    new_password = serializers.CharField(required=True)
    current_password = serializers.CharField(required=True)


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для модели Ingredient"""

    class Meta:
        fields = (
            'id',
            'name',
            'measurement_unit'
        )
        model = Ingredient


class IngredientRecipeReadSerializer(serializers.ModelSerializer):
    """Сериализатор для модели IngredientRecipe на вывод"""
    id = serializers.IntegerField(source='ingredient.id')
    name = serializers.CharField(source='ingredient.name')
    measurement_unit = serializers.CharField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        fields = (
            'id',
            'name',
            'measurement_unit',
            'amount'
        )
        model = IngredientRecipe


class IngredientRecipeWriteSerializer(serializers.ModelSerializer):
    """Сериализатор для модели IngredientRecipe на создание"""
    id = serializers.IntegerField(write_only=True)
    ingredient = IngredientSerializer(read_only=True)

    class Meta:
        fields = (
            'id',
            'ingredient',
            'amount'
        )
        model = IngredientRecipe


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор для модели Tag"""

    class Meta:
        fields = (
            'id',
            'name',
            'slug',
            'color'
        )
        model = Tag


class RecipeReadSerializer(serializers.ModelSerializer):
    """Сериализатор модели Recipe на вывод"""
    author = CustomUserSerializer(read_only=True)
    image = Base64ImageField()
    ingredients = IngredientRecipeReadSerializer(
        source="ingredientrecipe_set",
        many=True,
        read_only=True,
    )
    tags = TagSerializer(
        many=True,
        read_only=True
    )

    class Meta:
        fields = (
            'id',
            'author',
            'name',
            'image',
            'text',
            'ingredients',
            'tags',
            'cooking_time',
            'is_favorited',
            'is_in_shopping_cart'
        )
        model = Recipe


class RecipeWriteSerializer(serializers.ModelSerializer):
    """Сериализатор модели Recipe на создание"""
    author = SlugRelatedField(
        slug_field='username',
        read_only=True,
        default=serializers.CurrentUserDefault()
    )
    image = Base64ImageField()
    ingredients = IngredientRecipeWriteSerializer(
        many=True,
    )
    tags = PrimaryKeyRelatedField(
        many=True,
        queryset=Tag.objects.all()
    )
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        fields = (
            'id',
            'author',
            'name',
            'image',
            'text',
            'ingredients',
            'tags',
            'cooking_time',
            'is_favorited',
            'is_in_shopping_cart'
        )
        model = Recipe

    def get_is_favorited(self, obj):
        request = self.context.get('request')
        user = request.user
        return Favorite.objects.filter(recipe=obj, user=user).exists()

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get('request')
        user = request.user
        return ShoppingCart.objects.filter(recipe=obj, user=user).exists()

    def ingredients_for_recipe(self, recipe, ingredients):
        recipe_ingredient_list = []
        for ingredient in ingredients:
            current_ingredient = Ingredient.objects.get(
                pk=ingredient['id'])
            recipe_ingredient = IngredientRecipe(
                recipe=recipe,
                ingredient=current_ingredient,
                amount=ingredient['amount'])
            recipe_ingredient_list.append(recipe_ingredient)
        IngredientRecipe.objects.bulk_create(recipe_ingredient_list)

    @transaction.atomic
    def create(self, validated_data):
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.add(*tags)
        self.ingredients_for_recipe(recipe, ingredients)
        return recipe

    @transaction.atomic
    def update(self, instance, validated_data):
        instance.name = validated_data.get('name', instance.name)
        instance.image = validated_data.get('image', instance.image)
        instance.text = validated_data.get('text', instance.text)
        instance.cooking_time = validated_data.get(
            'cooking_time',
            instance.cooking_time
        )
        tags_data = validated_data.pop('tags')
        ingredients_data = validated_data.pop('ingredients')
        instance.tags.clear()
        instance.ingredients.clear()
        instance.tags.set(tags_data)
        self.ingredients_for_recipe(instance, ingredients_data)
        instance.save()
        return instance

    def validate_favorite(self, user, recipe):
        is_added = Favorite.objects.filter(
            user=user, recipe=recipe).exists()

        if is_added:
            raise serializers.ValidationError(
                {'detail': 'Рецепт уже добавлен в избранное'}
            )

    def validate_not_favorite(self, user, recipe):
        favorite = Favorite.objects.filter(user=user, recipe=recipe)
        if not favorite:
            raise serializers.ValidationError(
                {'detail': 'Рецепт не добавлен в избранное'}
            )
        return favorite

    def validate_shopping_cart(self, user, recipe):
        is_added = ShoppingCart.objects.filter(
            user=user, recipe=recipe).exists()
        if is_added:
            raise serializers.ValidationError(
                {'detail': 'Рецепт уже в списке покупок'}
            )

    def validate_not_shopping_cart(self, user, recipe):
        shopping_cart_item = ShoppingCart.objects.filter(
            recipe=recipe, user=user)
        if not shopping_cart_item:
            raise serializers.ValidationError(
                {'detail': 'Рецепт не в списке покупок'}
            )
        return shopping_cart_item

    def to_representation(self, instance):
        serializer = RecipeReadSerializer(instance)
        return serializer.data


class SubscribeRecipeSerializer(serializers.ModelSerializer):
    """Сериализатор для моделей Subscribe и ShoppingCart
    с данными из Recipe"""

    class Meta:
        fields = (
            'id',
            'name',
            'image',
            'cooking_time'
        )
        model = Recipe


class SubscribeSerializer(serializers.ModelSerializer):
    """Сериализатор для модели Subscribe"""
    email = serializers.EmailField(read_only=True)
    username = serializers.CharField(read_only=True)
    first_name = serializers.CharField(read_only=True)
    last_name = serializers.CharField(read_only=True)
    recipes = SubscribeRecipeSerializer(many=True, read_only=True)
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'recipes',
            'recipes_count'
        )
        model = CustomUser

    def get_recipes_count(self, obj):
        return obj.recipes.count()

    def validate_subscription(self, user, author):
        if user == author:
            raise serializers.ValidationError(
                {'detail': 'Нельзя подписаться на себя!'}
            )

        _, created = Subscribe.objects.get_or_create(
                user=user,
                following=author
        )
        if not created:
            raise serializers.ValidationError(
                {'detail': 'Пользователь уже подписан на данного автора'}
            )

    def validate_unsubscription(self, user, author):
        subscription = Subscribe.objects.filter(user=user, following=author)
        if not subscription:
            raise serializers.ValidationError(
                {'detail': 'Пользователь не подписан на данного автора'}
            )
        return subscription
