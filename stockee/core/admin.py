from django.contrib import admin
from .models import Stock, UserStockPreference, StockUpdate, NotificationLog


@admin.register(Stock)
class StockAdmin(admin.ModelAdmin):
    list_display = ('symbol', 'name', 'exchange', 'is_active', 'created_at')
    list_filter = ('exchange', 'is_active')
    search_fields = ('symbol', 'name')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(UserStockPreference)
class UserStockPreferenceAdmin(admin.ModelAdmin):
    list_display = ('user', 'stock', 'notification_frequency', 'is_active', 'created_at')
    list_filter = ('notification_frequency', 'is_active')
    search_fields = ('user__username', 'stock__symbol')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(StockUpdate)
class StockUpdateAdmin(admin.ModelAdmin):
    list_display = ('stock', 'price', 'change_percent', 'trend', 'created_at')
    list_filter = ('trend', 'created_at')
    search_fields = ('stock__symbol',)
    readonly_fields = ('created_at',)
    ordering = ('-created_at',)


@admin.register(NotificationLog)
class NotificationLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'stock', 'notification_type', 'status', 'sent_at')
    list_filter = ('notification_type', 'status', 'sent_at')
    search_fields = ('user__username', 'stock__symbol')
    readonly_fields = ('sent_at',)
    ordering = ('-sent_at',)
