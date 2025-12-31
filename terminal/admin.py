from django.contrib import admin
from .models import TerminalLinks, Transaction


@admin.register(TerminalLinks)
class TerminalLinksAdmin(admin.ModelAdmin):
    list_display = ('shop_domain', 'terminal_id', 'location_id', 'staff_member_id', 'created_at')
    list_filter = ('shop_domain', 'created_at')
    search_fields = ('shop_domain', 'terminal_id', 'location_id', 'staff_member_id', 'user_id', 'shop_id')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Shopify Information', {
            'fields': ('shop_domain', 'shop_id', 'location_id', 'staff_member_id', 'user_id')
        }),
        ('Terminal Information', {
            'fields': ('terminal_id', 'api_key')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('transaction_id', 'status', 'amount', 'shop_domain', 'location_id', 'created_at')
    list_filter = ('status', 'shop_domain', 'created_at')
    search_fields = ('transaction_id', 'shop_domain', 'location_id', 'staff_member_id')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Transaction Information', {
            'fields': ('transaction_id', 'status', 'amount', 'terminal_link')
        }),
        ('Shopify Information', {
            'fields': ('shop_domain', 'location_id', 'staff_member_id')
        }),
        ('Payment Details', {
            'fields': ('error_msg', 'receipt')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('terminal_link')
