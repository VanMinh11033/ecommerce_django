from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['username', 'email', 'first_name', 'last_name', 'phone', 'is_staff']
    list_filter = ['is_staff', 'is_superuser', 'is_active']
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Thông tin thêm', {'fields': ('phone', 'address', 'city', 'district', 'ward', 'avatar', 'date_of_birth')}),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Thông tin thêm', {'fields': ('phone', 'address', 'city', 'district', 'ward')}),
    )
