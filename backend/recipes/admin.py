from django.contrib import admin

from .models import Ingredient, IngredientRecipe, Recipe, Tag, TagRecipe


class IngredientAdmin(admin.ModelAdmin):
    """Модель ингредиента в админке"""
    list_display = ('name', 'measurement_unit')
    list_filter = ('name',)


class Ingredientline(admin.TabularInline):
    model = IngredientRecipe


class Tagline(admin.TabularInline):
    model = TagRecipe


class RecipeAdmin(admin.ModelAdmin):
    """Модель рецепта в админке"""
    list_display = ('author', 'name')
    list_filter = ('author', 'name', 'tags')
    inlines = [
        Ingredientline,
        Tagline
        ]


admin.site.register(Ingredient, IngredientAdmin)
admin.site.register(Tag)
admin.site.register(Recipe, RecipeAdmin)
admin.site.register(IngredientRecipe)
admin.site.register(TagRecipe)
