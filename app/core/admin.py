from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import Client, Domain, User


class DomainInline(admin.TabularInline):
    model = Domain
    extra = 1
    max_num = 5


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ('schema_name', 'name', 'paid_until', 'on_trial', 'created_on')
    list_filter = ('on_trial', 'paid_until')
    search_fields = ('schema_name', 'name')
    inlines = [DomainInline]
    readonly_fields = ('created_on',)


@admin.register(Domain)
class DomainAdmin(admin.ModelAdmin):
    list_display = ('domain', 'tenant', 'is_primary')
    list_filter = ('is_primary',)
    search_fields = ('domain', 'tenant__name')


@admin.register(User)
class CustomUserAdmin(BaseUserAdmin):
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal Info', {'fields': ('first_name', 'last_name', 'email', 'phone')}),
        ('Tenant Context', {'fields': ('tenant',)}),
        ('Permissions', {
            'fields': ('is_active', 'is_customer', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    
    list_display = ('email',  'phone','is_customer', 'is_staff', 'is_active','username', 'tenant',)
    list_editable = ( 'is_staff', 'is_customer','is_active')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'tenant')
    search_fields = ('email', 'username', 'phone')
    ordering = ('tenant', 'email')



   