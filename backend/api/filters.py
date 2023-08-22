from django_filters.rest_framework import (BooleanFilter, FilterSet,
                                           ModelMultipleChoiceFilter)
from recipes.models import Ingredient, Tag
from rest_framework.filters import SearchFilter
from django_filters import NumberFilter


class RecipeFilter(FilterSet):
    """Класс для фильтрации рецептов"""
    tags = ModelMultipleChoiceFilter(
        field_name='tags__slug',
        to_field_name='slug',
        queryset=Tag.objects.all()
    )
    author = NumberFilter(field_name='author__id')

    is_favorited = BooleanFilter(
        method='get_is_favorited')
    is_in_shopping_cart = BooleanFilter(
        method='get_is_in_shopping_cart')

    def get_is_favorited(self, queryset, name, value):
        if self.request.user.is_authenticated:
            return queryset.filter(recipe_favorite__user=self.request.user)
        return queryset

    def get_is_in_shopping_cart(self, queryset, name, value):
        if self.request.user.is_authenticated:
            return queryset.filter(recipe_in_cart__user=self.request.user)
        return queryset


class IngredientFilter(SearchFilter):
    """Класс для поиска ингредиентов в выпадающем списке"""
    search_param = 'name'

    class Meta:
        model = Ingredient
        fields = ('name',)
