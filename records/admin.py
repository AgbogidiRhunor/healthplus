from django.contrib import admin
from .models import AdministrationSession, SessionDrug


class SessionDrugInline(admin.TabularInline):
    model = SessionDrug
    extra = 0
    readonly_fields = ['drug', 'dosage']


@admin.register(AdministrationSession)
class AdministrationSessionAdmin(admin.ModelAdmin):
    list_display = ['id', 'patient', 'doctor', 'drug_count', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['patient__username', 'doctor__username']
    readonly_fields = ['created_at', 'updated_at']
    inlines = [SessionDrugInline]
