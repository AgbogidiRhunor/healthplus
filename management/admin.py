from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ['username', 'email', 'first_name', 'last_name', 'role', 'is_approved', 'is_active']
    list_filter = ['role', 'is_approved', 'is_active']
    list_editable = ['is_approved']
    search_fields = ['username', 'email', 'first_name', 'last_name']

    fieldsets = UserAdmin.fieldsets + (
        ('Health Plus Info', {
            'fields': ('role', 'is_approved', 'date_of_birth', 'gender', 'blood_group',
                       'phone', 'address', 'allergies', 'medical_conditions',
                       'specialization', 'license_number')
        }),
    )

    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Health Plus Info', {
            'fields': ('role', 'is_approved', 'first_name', 'last_name', 'email')
        }),
    )
