from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from users.models import CustomUser


class Ingredient(models.Model):
    """Модель ингредиента"""
    name = models.CharField(
        max_length=100,
        verbose_name='Название'
    )
    measurement_unit = models.CharField(
        max_length=50,
        verbose_name='Единица измерения'
    )


class Tag(models.Model):
    """Модель тега"""
    name = models.CharField(
        max_length=100,
        verbose_name='Название',
        unique=True
    )
    slug = models.SlugField(
        verbose_name='URL',
        unique=True,
    )
    color = models.CharField(
        max_length=7,
        unique=True
    )


class Recipe(models.Model):
    """Модель рецепта"""
    author = models.ForeignKey(
        CustomUser,
        related_name='recipes',
        on_delete=models.CASCADE
    )
    name = models.CharField(
        max_length=100,
        verbose_name='Название'
    )
    image = models.ImageField(
        upload_to='recipes/images/',
    )
    text = models.TextField(
        verbose_name='Описание'
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        verbose_name='Ингредиенты',
        through='IngredientRecipe'
    )
    tags = models.ManyToManyField(
        Tag,
        verbose_name='Тeг',
        through='TagRecipe'
    )
    cooking_time = models.PositiveIntegerField(
        verbose_name='Время приготовления',
        validators=[
            MinValueValidator(
                1,
                'Минимальное время приготовления - 1'
            ),
            MaxValueValidator(
                400,
                'Максимальное время приготовления - 400'
            )
        ]
    )

    def __str__(self):
        return self.name


class IngredientRecipe(models.Model):
    """Модель ингредиент-рецепт"""
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
    )
    amount = models.IntegerField(
        validators=[
            MinValueValidator(
                1,
                'Минимальное количество ингредиента - 1'
            ),
            MaxValueValidator(
                5000,
                'Максимальное количество ингредиента - 5000'
            )
        ]
    )


class TagRecipe(models.Model):
    """Модель тег-рецепт"""
    tag = models.ForeignKey(
        Tag,
        on_delete=models.CASCADE
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE
    )


class Subscribe(models.Model):
    """Модель подписки на автора"""
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='following',
    )
    following = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='followers',
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'following'],
                name='unique_user_following',
            )
        ]


class Favorite(models.Model):
    """Модель для избранных рецептов"""
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='user_favorite',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='recipe_favorite',
    )

    @classmethod
    def create(cls, user, recipe):
        item = cls(user=user, recipe=recipe)
        recipe.is_favorited = True
        recipe.save()
        item.save()
        return item


class ShoppingCart(models.Model):
    """Модель для списка покупок"""
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='user_in_cart',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='recipe_in_cart',
    )

    @classmethod
    def create(cls, user, recipe):
        item = cls(user=user, recipe=recipe)
        recipe.is_in_shopping_cart = True
        recipe.save()
        item.save()
        return item
