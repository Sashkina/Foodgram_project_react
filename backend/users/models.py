from django.contrib.auth.models import AbstractUser
from django.db import models


class CustomUser(AbstractUser):
    """Кастомная модель юзера"""
    username = models.CharField(
        max_length=250,
        verbose_name='Логин',
        unique=True,
    )
    password = models.CharField(
        max_length=250,
        verbose_name='Пароль'
    )
    email = models.EmailField(
        verbose_name='Email',
        unique=True
    )
    first_name = models.CharField(
        max_length=250,
        verbose_name='Имя'
    )
    last_name = models.CharField(
        max_length=250,
        verbose_name='Фамилия'
    )
    is_subscribed = models.BooleanField(default=False)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = [
        'username',
        'password',
        'first_name',
        'last_name'
    ]
