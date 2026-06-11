from django.contrib import admin
from .models import Invoice


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = (
        'invoice_number', 'lead', 'expert', 'amount_formatted',
        'status', 'created_at', 'paid_at'
    )
    list_filter = ('status', 'expert', 'created_at')
    search_fields = ('invoice_number', 'lead__name', 'lead__phone')
    readonly_fields = ('invoice_number', 'created_at', 'paid_at', 'zibal_track_id', 'payment_url', 'ref_number')
    date_hierarchy = 'created_at'
