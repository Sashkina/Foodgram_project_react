from django.http import HttpResponse
from djoser.views import UserViewSet
from rest_framework import viewsets, status
from rest_framework.generics import UpdateAPIView
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404

from recipes.models import (
    Ingredient,
    Tag,
    Recipe,
    Subscribe,
    Favorite,
    ShoppingCart
)
from .serializers import (
    CustomUserSerializer,
    PasswordSerializer,
    IngredientSerializer,
    TagSerializer,
    RecipeReadSerializer,
    RecipeWriteSerializer,
    SubscribeRecipeSerializer,
    SubscribeSerializer
)
from .permissions import AuthorOrReadOnly, ReadOnly
from users.models import CustomUser


class CustomUserViewSet(UserViewSet):
    """Эндпоинт для работы с моделью CustomUser"""
    queryset = CustomUser.objects.all()
    serializer_class = CustomUserSerializer

    @action(detail=False, methods=['GET'], permission_classes=[IsAuthenticated])
    def subscriptions(self, request):
        """Вывод всех подписок юзера"""
        user = request.user
        subscriptions = CustomUser.objects.filter(following__user=user)    
        serializer = SubscribeSerializer(
            subscriptions,
            many=True
        )
        queryset = self.paginate_queryset(serializer.data)
        return self.get_paginated_response(queryset)


class SetPasswordView(UpdateAPIView):
    """Эндпоинт для смены пароля (set_password)"""
    serializer_class = PasswordSerializer
    model = CustomUser
    permission_classes = (IsAuthenticated,)
    methods=['post']

    def get_object(self, queryset=None):
        obj = self.request.user
        return obj

    def update(self, request, *args, **kwargs):
        self.object = self.get_object()
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            if not self.object.check_password(serializer.data.get("current_password")):
                return Response(
                    {"current_password": ["Неверный пароль"]},
                    status=status.HTTP_400_BAD_REQUEST
                )
            self.object.set_password(serializer.data.get("new_password"))
            self.object.save()
            return Response({'status': 'password set'})
        return Response(status=status.HTTP_400_BAD_REQUEST)


class RecipeViewSet(viewsets.ModelViewSet):
    """Эндпоинт для работы с моделью Recipe"""
    queryset = Recipe.objects.all().order_by('-id')
    filter_backends = (DjangoFilterBackend,)
    filterset_fields = ('tags',)
    permission_classes = (AuthorOrReadOnly,) 

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def perform_update(self, serializer):
        super(RecipeViewSet, self).perform_update(serializer) 

    @action(detail=True, methods=['POST', 'DELETE'])
    def favorite(self, request, pk=None):
        """Добавляет рецепт в избранное"""
        user = request.user
        recipe = get_object_or_404(Recipe, pk=pk)

        if request.method == 'POST':
            is_added = Favorite.objects.filter(user=user, recipe=recipe).exists()

            if is_added:
                return Response(
                    {'detail': 'Рецепт уже добавлен в избранное'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            favorite = Favorite.objects.create(user=user, recipe=recipe)
            favorite.save()
            recipe.is_favorited = True
            recipe.save()
            return Response({'detail': 'Рецепт успешно добавлен в избранное'},
                            status=status.HTTP_201_CREATED)
        if request.method == 'DELETE':
            favorite = get_object_or_404(Favorite, user=user, recipe=recipe)

            favorite.delete()
            recipe.is_favorited = False
            recipe.save()
            return Response({'detail': 'Рецепт успешно удален из избранного'},
                            status=status.HTTP_204_NO_CONTENT)
        
    @action(detail=True, methods=['POST', 'DELETE'], permission_classes=[IsAuthenticated])
    def shopping_cart(self, request, pk=None):
        """Добавляет рецепт в список покупок"""
        recipe = get_object_or_404(Recipe, pk=pk)
        user = request.user
        
        if request.method == 'POST':
            if ShoppingCart.objects.filter(recipe=recipe, user=user).exists():
                return Response(
                    {'detail': 'Рецепт уже в списке покупок'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            ShoppingCart.objects.create(recipe=recipe, user=user)
            recipe.is_in_shopping_cart = True
            recipe.save()

            serializer = SubscribeRecipeSerializer(recipe)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        if request.method == 'DELETE':
            shopping_cart_item = ShoppingCart.objects.filter(recipe=recipe, user=user)
            if not shopping_cart_item:
                return Response(
                    {'detail': 'Рецепт не в списке покупок'},
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
                    ingredients[name]['quantity'] += ingredient_recipe.amount * quantity
                else:
                    ingredients[name] = {
                    'quantity': ingredient_recipe.amount * quantity,
                    'unit': unit
                }

        shopping_list = ""
        for name, ingredient_data in ingredients.items():
            shopping_list += f"{name} ({ingredient_data['unit']}) - {ingredient_data['quantity']}\n"
        response = HttpResponse(shopping_list, content_type='text/plain')
        response['Content-Disposition'] = 'attachment; filename="shopping_cart.txt"'
        return response


class IngredientViewSet(viewsets.ModelViewSet):
    """Эндпоинт для работы с моделью Ingredient"""
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    pagination_class = None


class TagViewSet(viewsets.ModelViewSet):
    """Эндпоинт для работы с моделью Tag"""
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None


class SubscribeViewSet(viewsets.ModelViewSet):
    """Эндпоинт для работы с моделью Subscribe"""
    queryset = CustomUser.objects.all()
    serializer_class = CustomUserSerializer
    permission_classes=[IsAuthenticated]

    @action(detail=True, methods=['POST', 'DELETE'])
    def subscribe(self, request, *args, **kwargs):
        """Подписка/отписка от автора"""
        author = self.get_object()
        user = request.user

        if request.method == 'POST':
            _, created = Subscribe.objects.get_or_create(
                user=user,
                following=author
            )
            if not created:
                return Response(
                    {'detail': 'Пользователь уже подписан на данного автора'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        
            serializer = SubscribeSerializer(
                author,
                context={'request': request}
            )
            author.is_subscribed = True
            author.save()
            return Response(serializer.data)
        
        if request.method == 'DELETE':
            subscription = Subscribe.objects.filter(user=user, following=author)
            if not subscription.exists():
                return Response(
                    {'detail': 'Пользователь не подписан на данного автора'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            subscription.delete()
            author.is_subscribed = False
            author.save()
            return Response(
                {'detail': 'Пользователь успешно отписан от данного автора'},
                status=status.HTTP_204_NO_CONTENT
            )
