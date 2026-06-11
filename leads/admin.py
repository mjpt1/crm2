from django.contrib import admin
from .models import Lead, LeadNote, UTMSource


@admin.register(UTMSource)
class UTMSourceAdmin(admin.ModelAdmin):
    list_display = ('name', 'utm_source', 'utm_medium', 'utm_campaign', 'token', 'is_active', 'created_at')
    list_filter = ('is_active',)
    readonly_fields = ('token',)


class LeadNoteInline(admin.TabularInline):
    model = LeadNote
    extra = 0
    readonly_fields = ('created_by', 'created_at')


@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone', 'status', 'assigned_to', 'utm_source', 'created_at')
    list_filter = ('status', 'assigned_to', 'utm_source')
    search_fields = ('name', 'phone', 'email')
    inlines = [LeadNoteInline]
    date_hierarchy = 'created_at'
