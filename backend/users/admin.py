from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import CustomUser


class CustomUserAdmin(UserAdmin):
    """Модель юзера в админке"""
    list_display = (
        'username',
        'password',
        'email',
        'first_name',
        'last_name'
    )
    list_filter = ('email', 'username')


admin.site.register(CustomUser, CustomUserAdmin)
