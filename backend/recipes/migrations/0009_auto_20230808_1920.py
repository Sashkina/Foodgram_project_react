# Generated by Django 3.2.3 on 2023-08-08 19:20

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('recipes', '0008_auto_20230807_0543'),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name='subscribe',
            name='unique_user_following',
        ),
        migrations.RenameField(
            model_name='subscribe',
            old_name='user',
            new_name='follower',
        ),
        migrations.AlterField(
            model_name='ingredientrecipe',
            name='amount',
            field=models.IntegerField(validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(400)]),
        ),
        migrations.AlterField(
            model_name='recipe',
            name='cooking_time',
            field=models.PositiveIntegerField(verbose_name='Время приготовления'),
        ),
        migrations.AlterField(
            model_name='recipe',
            name='ingredients',
            field=models.ManyToManyField(through='recipes.IngredientRecipe', to='recipes.Ingredient', verbose_name='Ингредиенты'),
        ),
        migrations.AlterField(
            model_name='recipe',
            name='tags',
            field=models.ManyToManyField(through='recipes.TagRecipe', to='recipes.Tag', verbose_name='Тeг'),
        ),
        migrations.AddConstraint(
            model_name='subscribe',
            constraint=models.UniqueConstraint(fields=('follower', 'following'), name='unique_follower_following'),
        ),
    ]
