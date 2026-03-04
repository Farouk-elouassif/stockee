from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator


class Stock(models.Model):
    """
    Represents a stock/ticker that can be tracked.
    """
    CURRENCY_CHOICES = [
        ('USD', 'US Dollar'),
        ('EUR', 'Euro'),
        ('GBP', 'British Pound'),
        ('JPY', 'Japanese Yen'),
        ('CAD', 'Canadian Dollar'),
    ]

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
    sector = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Industry sector (e.g., Technology, Healthcare)"
    )
    currency = models.CharField(
        max_length=3,
        choices=CURRENCY_CHOICES,
        default='USD',
        help_text="Trading currency"
    )
    market_cap = models.BigIntegerField(
        blank=True,
        null=True,
        help_text="Market capitalization in currency units"
    )
    last_price = models.DecimalField(
        max_digits=12,
        decimal_places=4,
        blank=True,
        null=True,
        help_text="Cached last known price for quick access"
    )
    last_price_updated = models.DateTimeField(
        blank=True,
        null=True,
        help_text="When last_price was last updated"
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
        indexes = [
            models.Index(fields=['sector']),
            models.Index(fields=['exchange']),
        ]

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
    Stores historical stock updates with OHLCV data and AI-generated analysis.
    """
    TREND_CHOICES = [
        ('up', 'Up'),
        ('down', 'Down'),
        ('neutral', 'Neutral'),
    ]

    DATA_SOURCE_CHOICES = [
        ('alpha_vantage', 'Alpha Vantage'),
        ('yahoo', 'Yahoo Finance'),
        ('polygon', 'Polygon.io'),
        ('finnhub', 'Finnhub'),
        ('manual', 'Manual Entry'),
    ]

    TIMEFRAME_CHOICES = [
        ('1m', '1 Minute'),
        ('5m', '5 Minutes'),
        ('15m', '15 Minutes'),
        ('1h', '1 Hour'),
        ('4h', '4 Hours'),
        ('1d', '1 Day'),
        ('1w', '1 Week'),
    ]

    stock = models.ForeignKey(
        Stock,
        on_delete=models.CASCADE,
        related_name='updates'
    )
    # OHLCV Data
    open_price = models.DecimalField(
        max_digits=12,
        decimal_places=4,
        validators=[MinValueValidator(0)],
        help_text="Opening price"
    )
    high_price = models.DecimalField(
        max_digits=12,
        decimal_places=4,
        validators=[MinValueValidator(0)],
        help_text="Highest price in the period"
    )
    low_price = models.DecimalField(
        max_digits=12,
        decimal_places=4,
        validators=[MinValueValidator(0)],
        help_text="Lowest price in the period"
    )
    close_price = models.DecimalField(
        max_digits=12,
        decimal_places=4,
        validators=[MinValueValidator(0)],
        help_text="Closing price"
    )
    volume = models.BigIntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        help_text="Trading volume"
    )
    # Legacy fields (kept for compatibility)
    price = models.DecimalField(
        max_digits=12,
        decimal_places=4,
        validators=[MinValueValidator(0)],
        help_text="Current/closing stock price"
    )
    previous_price = models.DecimalField(
        max_digits=12,
        decimal_places=4,
        validators=[MinValueValidator(0)],
        null=True,
        blank=True,
        help_text="Previous closing price"
    )
    change_percent = models.DecimalField(
        max_digits=8,
        decimal_places=4,
        help_text="Percentage change (can be negative)"
    )
    trend = models.CharField(
        max_length=10,
        choices=TREND_CHOICES,
        help_text="Overall trend direction"
    )
    # Metadata
    timeframe = models.CharField(
        max_length=5,
        choices=TIMEFRAME_CHOICES,
        default='1d',
        help_text="Data timeframe/interval"
    )
    timestamp = models.DateTimeField(
        db_index=True,
        help_text="Actual market timestamp for this data point"
    )
    data_source = models.CharField(
        max_length=20,
        choices=DATA_SOURCE_CHOICES,
        default='yahoo',
        help_text="Source of this price data"
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
        ordering = ['-timestamp']
        verbose_name = 'Stock Update'
        verbose_name_plural = 'Stock Updates'
        indexes = [
            models.Index(fields=['stock', '-timestamp']),
            models.Index(fields=['stock', 'timeframe', '-timestamp']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['stock', 'timestamp', 'timeframe'],
                name='unique_stock_timestamp_timeframe'
            )
        ]

    def __str__(self):
        return f"{self.stock.symbol} - {self.trend} {self.change_percent}% @ {self.timestamp.strftime('%Y-%m-%d %H:%M')}"


class UserProfile(models.Model):
    """
    Extended user profile for notification preferences and settings.
    """
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile'
    )
    timezone = models.CharField(
        max_length=50,
        default='UTC',
        help_text="User's timezone for notifications (e.g., 'America/New_York')"
    )
    email_notifications = models.BooleanField(
        default=True,
        help_text="Whether to receive email notifications"
    )
    webhook_url = models.URLField(
        blank=True,
        null=True,
        help_text="Webhook URL for notifications (Slack, Discord, etc.)"
    )
    webhook_secret = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Secret for signing webhook payloads"
    )
    daily_alert_limit = models.PositiveIntegerField(
        default=50,
        validators=[MaxValueValidator(500)],
        help_text="Maximum alerts per day"
    )
    alerts_sent_today = models.PositiveIntegerField(
        default=0,
        help_text="Counter for alerts sent today (reset daily)"
    )
    last_alert_reset = models.DateField(
        auto_now_add=True,
        help_text="Last date the alert counter was reset"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'User Profile'
        verbose_name_plural = 'User Profiles'

    def __str__(self):
        return f"Profile: {self.user.username}"


class AlertRule(models.Model):
    """
    User-defined alert rules for stock price conditions.
    """
    ALERT_TYPE_CHOICES = [
        ('price_above', 'Price Above'),
        ('price_below', 'Price Below'),
        ('percent_change_up', 'Percent Change Up'),
        ('percent_change_down', 'Percent Change Down'),
        ('volume_spike', 'Volume Spike'),
    ]

    TIME_WINDOW_CHOICES = [
        ('1h', '1 Hour'),
        ('4h', '4 Hours'),
        ('1d', '1 Day'),
        ('1w', '1 Week'),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='alert_rules'
    )
    stock = models.ForeignKey(
        Stock,
        on_delete=models.CASCADE,
        related_name='alert_rules'
    )
    name = models.CharField(
        max_length=100,
        blank=True,
        help_text="Optional friendly name for this alert"
    )
    alert_type = models.CharField(
        max_length=20,
        choices=ALERT_TYPE_CHOICES,
        help_text="Type of alert condition"
    )
    threshold_value = models.DecimalField(
        max_digits=12,
        decimal_places=4,
        help_text="Threshold value (price or percentage depending on alert_type)"
    )
    time_window = models.CharField(
        max_length=5,
        choices=TIME_WINDOW_CHOICES,
        default='1d',
        help_text="Time window for percentage-based alerts"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this alert is enabled"
    )
    is_one_time = models.BooleanField(
        default=False,
        help_text="If true, deactivate after first trigger"
    )
    cooldown_minutes = models.PositiveIntegerField(
        default=60,
        help_text="Minimum minutes between repeated triggers"
    )
    last_triggered_at = models.DateTimeField(
        blank=True,
        null=True,
        help_text="When this alert was last triggered"
    )
    trigger_count = models.PositiveIntegerField(
        default=0,
        help_text="Total times this alert has been triggered"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Alert Rule'
        verbose_name_plural = 'Alert Rules'
        indexes = [
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['stock', 'is_active', 'alert_type']),
        ]

    def __str__(self):
        name = self.name or f"{self.get_alert_type_display()} {self.threshold_value}"
        return f"{self.user.username} - {self.stock.symbol}: {name}"


class TriggeredAlert(models.Model):
    """
    Records of alerts that have been triggered.
    """
    alert_rule = models.ForeignKey(
        AlertRule,
        on_delete=models.CASCADE,
        related_name='triggered_alerts'
    )
    stock_update = models.ForeignKey(
        StockUpdate,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='triggered_alerts',
        help_text="The stock update that triggered this alert"
    )
    triggered_value = models.DecimalField(
        max_digits=12,
        decimal_places=4,
        help_text="The actual value when the alert was triggered"
    )
    threshold_value = models.DecimalField(
        max_digits=12,
        decimal_places=4,
        help_text="The threshold value at time of trigger (snapshot)"
    )
    ai_analysis = models.TextField(
        blank=True,
        null=True,
        help_text="AI-generated explanation of why this alert matters"
    )
    is_acknowledged = models.BooleanField(
        default=False,
        help_text="Whether the user has acknowledged this alert"
    )
    acknowledged_at = models.DateTimeField(
        blank=True,
        null=True
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True
    )

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Triggered Alert'
        verbose_name_plural = 'Triggered Alerts'
        indexes = [
            models.Index(fields=['alert_rule', '-created_at']),
        ]

    def __str__(self):
        return f"{self.alert_rule.stock.symbol} triggered @ {self.triggered_value} ({self.created_at.strftime('%Y-%m-%d %H:%M')})"


class LLMUsageLog(models.Model):
    """
    Tracks LLM API usage for cost monitoring and debugging.
    """
    PROMPT_TYPE_CHOICES = [
        ('alert_analysis', 'Alert Analysis'),
        ('market_summary', 'Market Summary'),
        ('news_digest', 'News Digest'),
        ('price_explanation', 'Price Explanation'),
        ('portfolio_insight', 'Portfolio Insight'),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='llm_usage',
        help_text="User who initiated this request (null for system calls)"
    )
    stock = models.ForeignKey(
        Stock,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='llm_usage',
        help_text="Related stock if applicable"
    )
    triggered_alert = models.ForeignKey(
        TriggeredAlert,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='llm_usage',
        help_text="Related triggered alert if applicable"
    )
    prompt_type = models.CharField(
        max_length=20,
        choices=PROMPT_TYPE_CHOICES,
        help_text="Type of prompt/analysis"
    )
    model_name = models.CharField(
        max_length=50,
        help_text="LLM model used (e.g., 'gpt-4', 'claude-3-opus')"
    )
    prompt_text = models.TextField(
        help_text="The prompt sent to the LLM"
    )
    response_text = models.TextField(
        blank=True,
        null=True,
        help_text="The response from the LLM"
    )
    input_tokens = models.PositiveIntegerField(
        default=0,
        help_text="Number of input tokens"
    )
    output_tokens = models.PositiveIntegerField(
        default=0,
        help_text="Number of output tokens"
    )
    cost_usd = models.DecimalField(
        max_digits=10,
        decimal_places=6,
        default=0,
        help_text="Estimated cost in USD"
    )
    latency_ms = models.PositiveIntegerField(
        default=0,
        help_text="Response latency in milliseconds"
    )
    is_success = models.BooleanField(
        default=True,
        help_text="Whether the LLM call was successful"
    )
    error_message = models.TextField(
        blank=True,
        null=True,
        help_text="Error message if the call failed"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True
    )

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'LLM Usage Log'
        verbose_name_plural = 'LLM Usage Logs'
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['prompt_type', '-created_at']),
            models.Index(fields=['model_name', '-created_at']),
        ]

    def __str__(self):
        user_str = self.user.username if self.user else "System"
        return f"{user_str} - {self.prompt_type} ({self.model_name}) @ {self.created_at.strftime('%Y-%m-%d %H:%M')}"


class NotificationLog(models.Model):
    """
    Tracks all notifications sent to users with retry support.
    """
    NOTIFICATION_TYPE_CHOICES = [
        ('email', 'Email'),
        ('webhook', 'Webhook'),
        ('sms', 'SMS'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('sending', 'Sending'),
        ('sent', 'Sent'),
        ('failed', 'Failed'),
        ('retry', 'Retry Scheduled'),
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
        on_delete=models.SET_NULL,
        related_name='notifications',
        null=True,
        blank=True
    )
    triggered_alert = models.ForeignKey(
        TriggeredAlert,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='notifications',
        help_text="The triggered alert that caused this notification"
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
    retry_count = models.PositiveIntegerField(
        default=0,
        help_text="Number of retry attempts"
    )
    max_retries = models.PositiveIntegerField(
        default=3,
        help_text="Maximum retry attempts before giving up"
    )
    next_retry_at = models.DateTimeField(
        blank=True,
        null=True,
        help_text="Scheduled time for next retry attempt"
    )
    sent_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True
    )
    delivered_at = models.DateTimeField(
        blank=True,
        null=True,
        help_text="When the notification was successfully delivered"
    )

    class Meta:
        ordering = ['-sent_at']
        verbose_name = 'Notification Log'
        verbose_name_plural = 'Notification Logs'
        indexes = [
            models.Index(fields=['user', '-sent_at']),
            models.Index(fields=['status', '-sent_at']),
            models.Index(fields=['status', 'next_retry_at']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.stock.symbol} ({self.status}) @ {self.sent_at.strftime('%Y-%m-%d %H:%M')}"
