# Generated by Django 3.2.3 on 2023-08-13 19:06

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('recipes', '0016_auto_20230810_1003'),
    ]

    operations = [
        migrations.AlterField(
            model_name='ingredientrecipe',
            name='amount',
            field=models.IntegerField(validators=[django.core.validators.MinValueValidator(1, 'Минимальное количество ингредиента - 1'), django.core.validators.MaxValueValidator(5000, 'Максимальное количество ингредиента - 5000')]),
        ),
        migrations.AlterField(
            model_name='recipe',
            name='cooking_time',
            field=models.PositiveIntegerField(validators=[django.core.validators.MinValueValidator(1, 'Минимальное время приготовления - 1'), django.core.validators.MaxValueValidator(400, 'Максимальное время приготовления - 400')], verbose_name='Время приготовления'),
        ),
    ]