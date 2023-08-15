from django.db import transaction
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters import FilterSet, filters
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet
from recipes.models import (Favorite, Ingredient, Recipe, ShoppingCart,
                            Subscribe, Tag)
from rest_framework import serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.generics import UpdateAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from users.models import CustomUser

from .pagination import RecipePagination
from .permissions import AuthorOrReadOnly, ReadOnly
from .serializers import (CustomUserSerializer, IngredientSerializer,
                          PasswordSerializer, RecipeReadSerializer,
                          RecipeWriteSerializer, SubscribeRecipeSerializer,
                          SubscribeSerializer, TagSerializer)


class CustomUserViewSet(UserViewSet):
    """Эндпоинт для работы с моделью CustomUser"""
    queryset = CustomUser.objects.all()
    serializer_class = CustomUserSerializer
    pagination_class = RecipePagination

    @action(
        detail=False,
        methods=['GET'],
        permission_classes=[IsAuthenticated]
    )
    def subscriptions(self, request):
        """Вывод всех подписок юзера"""
        user = request.user
        subscriptions = Subscribe.objects.filter(
            user=user
        ).select_related('following')
        serializer = SubscribeSerializer(
            [subscription.following for subscription in subscriptions],
            many=True
        )
        queryset = self.paginate_queryset(serializer.data)
        return self.get_paginated_response(queryset)


class SetPasswordView(UpdateAPIView):
    """Эндпоинт для смены пароля (set_password)"""
    serializer_class = PasswordSerializer
    model = CustomUser
    permission_classes = (IsAuthenticated,)

    def get_object(self, queryset=None):
        obj = self.request.user
        return obj

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            if not self.object.check_password(
                serializer.data.get('current_password')
            ):
                return Response(
                    {'current_password': ['Неверный пароль']},
                    status=status.HTTP_400_BAD_REQUEST
                )
            self.object.set_password(serializer.data.get('new_password'))
            self.object.save()
            return Response({'status': 'password set'})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class RecipeFilter(FilterSet):
    tags = filters.ModelMultipleChoiceFilter(
        field_name='tags__slug',
        to_field_name='slug',
        queryset=Tag.objects.all()
    )
    is_favorited = filters.BooleanFilter(
        method='get_is_favorited')
    is_in_shopping_cart = filters.BooleanFilter(
        method='get_is_in_shopping_cart')

    def get_is_favorited(self, queryset, name, value):
        if self.request.user.is_authenticated:
            return queryset.filter(favorite__user=self.request.user)
        return queryset

    def get_is_in_shopping_cart(self, queryset, name, value):
        if self.request.user.is_authenticated:
            return queryset.filter(in_cart__user=self.request.user)
        return queryset


class RecipeViewSet(viewsets.ModelViewSet):
    """Эндпоинт для работы с моделью Recipe"""
    queryset = Recipe.objects.all().order_by('-id')
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter
    permission_classes = (AuthorOrReadOnly,)
    pagination_class = RecipePagination

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def perform_update(self, serializer):
        super(RecipeViewSet, self).perform_update(serializer)

    @transaction.atomic
    @action(detail=True, methods=['POST', 'DELETE'])
    def favorite(self, request, pk=None):
        """Добавляет рецепт в избранное"""
        user = request.user
        recipe = get_object_or_404(Recipe, pk=pk)
        serializer = RecipeWriteSerializer()

        if request.method == 'POST':
            try:
                serializer.validate_favorite(user, recipe)
            except serializers.ValidationError as error:
                return Response(
                    error.detail,
                    status=status.HTTP_400_BAD_REQUEST
                )

            favorite = Favorite.create(user=user, recipe=recipe)

            return Response({'detail': 'Рецепт успешно добавлен в избранное'},
                            status=status.HTTP_201_CREATED)
        if request.method == 'DELETE':
            try:
                favorite = serializer.validate_not_favorite(user, recipe)
            except serializers.ValidationError as error:
                return Response(
                    error.detail,
                    status=status.HTTP_400_BAD_REQUEST
                )

            favorite.delete()
            recipe.is_favorited = False
            recipe.save()
            return Response({'detail': 'Рецепт успешно удален из избранного'},
                            status=status.HTTP_204_NO_CONTENT)

    @transaction.atomic
    @action(detail=True,
            methods=['POST', 'DELETE'],
            permission_classes=[IsAuthenticated])
    def shopping_cart(self, request, pk=None):
        """Добавляет рецепт в список покупок"""
        recipe = get_object_or_404(Recipe, pk=pk)
        user = request.user
        serializer = RecipeWriteSerializer()

        if request.method == 'POST':
            try:
                serializer.validate_shopping_cart(user, recipe)
            except serializers.ValidationError as error:
                return Response(
                    error.detail,
                    status=status.HTTP_400_BAD_REQUEST
                )

            ShoppingCart.create(user=user, recipe=recipe)

            serializer = SubscribeRecipeSerializer(recipe)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        if request.method == 'DELETE':
            try:
                shopping_cart_item = serializer.validate_not_shopping_cart(
                    user, recipe)
            except serializers.ValidationError as error:
                return Response(
                    error.detail,
                    status=status.HTTP_400_BAD_REQUEST
                )

            shopping_cart_item.delete()
            recipe.is_in_shopping_cart = False
            recipe.save()
            return Response(
                {'detail': 'Рецепт успешно удален из списка покупок'},
                status=status.HTTP_204_NO_CONTENT
            )

    def get_serializer_class(self):
        """Определяет какой сериализатор будет использоваться
              для разных типов запроса"""
        if self.action in ('list', 'retrieve'):
            return RecipeReadSerializer
        return RecipeWriteSerializer

    def get_permissions(self):
        """Определяет какой пермишен будет использоваться"""
        if self.action == 'retrieve':
            return (ReadOnly(),)
        return super().get_permissions()

    def download_shopping_cart(self, request):
        """Предлагает загрузить список покупок"""
        shopping_cart = request.session.get('shopping_cart', {})
        ingredients = {}

        for recipe_id, quantity in shopping_cart.items():
            recipe = Recipe.objects.get(pk=recipe_id)
            for ingredient_recipe in recipe.ingredientrecipe_set.all():
                ingredient = ingredient_recipe.ingredient
                name = ingredient.name
                unit = ingredient.measurement_unit
                if name in ingredients:
                    ingredients[name]['quantity'] \
                        += ingredient_recipe.amount \
                        * quantity
                else:
                    ingredients[name] = {
                        'quantity': ingredient_recipe.amount * quantity,
                        'unit': unit
                    }

        shopping_list = ""
        for name, ingredient_data in ingredients.items():
            shopping_list += f"{name} ({ingredient_data['unit']}) \
                - {ingredient_data['quantity']}\n"
        response = HttpResponse(shopping_list, content_type='text/plain')
        response['Content-Disposition'] \
            = 'attachment; filename="shopping_cart.txt"'
        return response


class IngredientViewSet(viewsets.ModelViewSet):
    """Эндпоинт для работы с моделью Ingredient"""
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer


class TagViewSet(viewsets.ModelViewSet):
    """Эндпоинт для работы с моделью Tag"""
    queryset = Tag.objects.all()
    serializer_class = TagSerializer


class SubscribeViewSet(viewsets.ModelViewSet):
    """Эндпоинт для работы с моделью Subscribe"""
    queryset = CustomUser.objects.all()
    serializer_class = CustomUserSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = RecipePagination

    @action(detail=True, methods=['POST', 'DELETE'])
    def subscribe(self, request, *args, **kwargs):
        """Подписка/отписка от автора"""
        author = self.get_object()
        user = request.user
        serializer = SubscribeSerializer()

        if request.method == 'POST':
            try:
                serializer.validate_subscription(user, author)
            except serializers.ValidationError as error:
                return Response(
                    error.detail,
                    status=status.HTTP_400_BAD_REQUEST
                )

            serializer = SubscribeSerializer(
                author,
                context={'request': request}
            )
            author.is_subscribed = True
            author.save()
            return Response(serializer.data)

        if request.method == 'DELETE':
            try:
                subscription = serializer.validate_unsubscription(user, author)
            except serializers.ValidationError as error:
                return Response(
                    error.detail,
                    status=status.HTTP_400_BAD_REQUEST
                )

            subscription.delete()
            author.is_subscribed = False
            author.save()
            return Response(
                {'detail': 'Пользователь успешно отписан от данного автора'},
                status=status.HTTP_204_NO_CONTENT
            )
