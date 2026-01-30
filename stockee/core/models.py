from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator


class Stock(models.Model):
    """
    Represents a stock/ticker that can be tracked.
    """
    symbol = models.CharField(
        max_length=10,
        unique=True,
        db_index=True,
        help_text="Stock ticker symbol (e.g., AAPL, TSLA)"
    )
    name = models.CharField(
        max_length=255,
        help_text="Full company name"
    )
    exchange = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="Stock exchange (e.g., NASDAQ, NYSE)"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this stock is actively tracked"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['symbol']
        verbose_name = 'Stock'
        verbose_name_plural = 'Stocks'

    def __str__(self):
        return f"{self.symbol} - {self.name}"


class UserStockPreference(models.Model):
    """
    Tracks which stocks a user wants to monitor and notification preferences.
    """
    FREQUENCY_CHOICES = [
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='stock_preferences'
    )
    stock = models.ForeignKey(
        Stock,
        on_delete=models.CASCADE,
        related_name='user_preferences'
    )
    notification_frequency = models.CharField(
        max_length=10,
        choices=FREQUENCY_CHOICES,
        default='daily',
        help_text="How often to receive updates"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether notifications are enabled for this stock"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['user', 'stock']
        ordering = ['-created_at']
        verbose_name = 'User Stock Preference'
        verbose_name_plural = 'User Stock Preferences'

    def __str__(self):
        return f"{self.user.username} - {self.stock.symbol} ({self.notification_frequency})"


class StockUpdate(models.Model):
    """
    Stores historical stock updates with price changes and AI-generated analysis.
    """
    TREND_CHOICES = [
        ('up', 'Up'),
        ('down', 'Down'),
        ('neutral', 'Neutral'),
    ]

    stock = models.ForeignKey(
        Stock,
        on_delete=models.CASCADE,
        related_name='updates'
    )
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text="Current stock price"
    )
    previous_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        null=True,
        blank=True,
        help_text="Previous closing price"
    )
    change_percent = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        help_text="Percentage change (can be negative)"
    )
    trend = models.CharField(
        max_length=10,
        choices=TREND_CHOICES,
        help_text="Overall trend direction"
    )
    ai_analysis = models.TextField(
        blank=True,
        null=True,
        help_text="AI-generated explanation of the price movement"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True
    )

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Stock Update'
        verbose_name_plural = 'Stock Updates'
        indexes = [
            models.Index(fields=['stock', '-created_at']),
        ]

    def __str__(self):
        return f"{self.stock.symbol} - {self.trend} {self.change_percent}% @ {self.created_at.strftime('%Y-%m-%d %H:%M')}"


class NotificationLog(models.Model):
    """
    Tracks all notifications sent to users.
    """
    NOTIFICATION_TYPE_CHOICES = [
        ('email', 'Email'),
        ('webhook', 'Webhook'),
        ('sms', 'SMS'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('failed', 'Failed'),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='notifications'
    )
    stock = models.ForeignKey(
        Stock,
        on_delete=models.CASCADE,
        related_name='notifications'
    )
    stock_update = models.ForeignKey(
        StockUpdate,
        on_delete=models.CASCADE,
        related_name='notifications',
        null=True,
        blank=True
    )
    notification_type = models.CharField(
        max_length=10,
        choices=NOTIFICATION_TYPE_CHOICES,
        default='email'
    )
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='pending'
    )
    message = models.TextField(
        blank=True,
        help_text="Notification message content"
    )
    error_message = models.TextField(
        blank=True,
        null=True,
        help_text="Error details if notification failed"
    )
    sent_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True
    )

    class Meta:
        ordering = ['-sent_at']
        verbose_name = 'Notification Log'
        verbose_name_plural = 'Notification Logs'
        indexes = [
            models.Index(fields=['user', '-sent_at']),
            models.Index(fields=['status', '-sent_at']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.stock.symbol} ({self.status}) @ {self.sent_at.strftime('%Y-%m-%d %H:%M')}"
