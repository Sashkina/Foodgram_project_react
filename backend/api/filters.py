import django_filters.filters as df_filters
from django_filters import FilterSet
from recipes.models import Ingredient, Tag
from rest_framework import filters as drf_filters


class RecipeFilter(FilterSet):
    """Класс для фильтрации рецептов"""
    tags = df_filters.ModelMultipleChoiceFilter(
        field_name='tags__slug',
        to_field_name='slug',
        queryset=Tag.objects.all()
    )
    
    is_favorited = df_filters.BooleanFilter(
        method='get_is_favorited')
    is_in_shopping_cart = df_filters.BooleanFilter(
        method='get_is_in_shopping_cart')

    def get_is_favorited(self, queryset, name, value):
        if self.request.user.is_authenticated:
            return queryset.filter(user_favorite__user=self.request.user)
        return queryset

    def get_is_in_shopping_cart(self, queryset, name, value):
        if self.request.user.is_authenticated:
            return queryset.filter(user_in_cart__user=self.request.user)
        return queryset


class IngredientFilter(drf_filters.SearchFilter):
    """Класс для поиска ингредиентов в выпадающем списке"""
    search_param = 'name'

    class Meta:
        model = Ingredient
        fields = ('name',)
