from django.contrib import admin
from .models import Drug

@admin.register(Drug)
class DrugAdmin(admin.ModelAdmin):
    list_display = ['name', 'strength', 'dosage_form', 'manufacturer', 'created_at']
    search_fields = ['name', 'manufacturer']
    list_filter = ['dosage_form']
