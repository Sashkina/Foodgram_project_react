from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    CustomUserViewSet,
    SetPasswordView,
    IngredientViewSet,
    RecipeViewSet,
    TagViewSet,
    SubscribeViewSet,
)

router = DefaultRouter()

router.register(r'users', CustomUserViewSet, basename='users')
router.register(r'users', SubscribeViewSet, basename='subscribe')
router.register(r'recipes', RecipeViewSet, basename='recipes')
router.register(
    r'ingredients',
    IngredientViewSet,
    basename='ingredients'
)
router.register(r'tags', TagViewSet, basename='tags')

urlpatterns = [
    path(
        'users/set_password/',
        SetPasswordView.as_view,
        name='password'
    ),
    path('recipes/download_shopping_cart/', RecipeViewSet.as_view({'get': 'download_shopping_cart'})),
    path('', include(router.urls)),
    path('', include('djoser.urls')),
    path('auth/', include('djoser.urls.authtoken')),
]
