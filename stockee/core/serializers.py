from rest_framework import serializers
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from rest_framework.validators import UniqueValidator
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .models import UserProfile, Stock, StockUpdate, UserStockPreference


class UserProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for UserProfile model.
    """
    class Meta:
        model = UserProfile
        fields = (
            'role', 'timezone', 'email_notifications', 'webhook_url',
            'daily_alert_limit', 'alerts_sent_today', 'created_at', 'updated_at'
        )
        read_only_fields = ('alerts_sent_today', 'created_at', 'updated_at')


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for user details with profile.
    """
    profile = UserProfileSerializer(read_only=True)

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'date_joined', 'profile')
        read_only_fields = ('id', 'date_joined')


class UserUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating user details.
    """
    profile = UserProfileSerializer(required=False)

    class Meta:
        model = User
        fields = ('email', 'first_name', 'last_name', 'profile')

    def update(self, instance, validated_data):
        profile_data = validated_data.pop('profile', None)
        
        # Update user fields
        instance.email = validated_data.get('email', instance.email)
        instance.first_name = validated_data.get('first_name', instance.first_name)
        instance.last_name = validated_data.get('last_name', instance.last_name)
        instance.save()

        # Update profile fields if provided
        if profile_data and hasattr(instance, 'profile'):
            profile = instance.profile
            for attr, value in profile_data.items():
                if attr not in ('alerts_sent_today', 'created_at', 'updated_at'):
                    setattr(profile, attr, value)
            profile.save()

        return instance


class RegisterSerializer(serializers.ModelSerializer):
    """
    Serializer for user registration.
    """
    email = serializers.EmailField(
        required=True,
        validators=[UniqueValidator(queryset=User.objects.all())]
    )
    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password],
        style={'input_type': 'password'}
    )
    password2 = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'},
        label='Confirm Password'
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'password', 'password2', 'first_name', 'last_name')
        extra_kwargs = {
            'first_name': {'required': False},
            'last_name': {'required': False}
        }

    def validate(self, attrs):
        """
        Validate that passwords match.
        """
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({
                "password": "Password fields didn't match."
            })
        return attrs

    def create(self, validated_data):
        """
        Create and return a new user with encrypted password and profile.
        """
        validated_data.pop('password2')
        
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', '')
        )
        
        # Create UserProfile with default role='user'
        UserProfile.objects.create(user=user, role='user')
        
        return user


class ChangePasswordSerializer(serializers.Serializer):
    """
    Serializer for changing password.
    """
    old_password = serializers.CharField(
        required=True,
        write_only=True,
        style={'input_type': 'password'}
    )
    new_password = serializers.CharField(
        required=True,
        write_only=True,
        validators=[validate_password],
        style={'input_type': 'password'}
    )
    new_password2 = serializers.CharField(
        required=True,
        write_only=True,
        style={'input_type': 'password'},
        label='Confirm New Password'
    )

    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password2']:
            raise serializers.ValidationError({
                "new_password": "New password fields didn't match."
            })
        return attrs

    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Old password is incorrect.")
        return value


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Custom JWT token serializer that includes user info in response.
    """
    def validate(self, attrs):
        data = super().validate(attrs)
        
        # Add user info to response
        user = self.user
        data['user'] = {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
        }
        
        # Add profile info if exists
        if hasattr(user, 'profile'):
            data['user']['profile'] = {
                'role': user.profile.role,
                'timezone': user.profile.timezone,
                'email_notifications': user.profile.email_notifications,
            }
        
        return data


# =============================================================================
# Stock Serializers
# =============================================================================

class StockListSerializer(serializers.ModelSerializer):
    """
    Lightweight serializer for stock list views.
    """
    class Meta:
        model = Stock
        fields = (
            'id', 'symbol', 'name', 'exchange', 'sector', 
            'currency', 'last_price', 'last_price_updated'
        )
        read_only_fields = fields


class StockDetailSerializer(serializers.ModelSerializer):
    """
    Full serializer for stock detail view with recent updates.
    """
    recent_updates = serializers.SerializerMethodField()

    class Meta:
        model = Stock
        fields = (
            'id', 'symbol', 'name', 'exchange', 'sector', 'currency',
            'market_cap', 'last_price', 'last_price_updated', 'is_active',
            'created_at', 'updated_at', 'recent_updates'
        )
        read_only_fields = fields

    def get_recent_updates(self, obj):
        """Get the last 30 stock updates."""
        updates = obj.updates.all()[:30]
        return StockUpdateSerializer(updates, many=True).data


class StockCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating/updating stocks (admin only).
    """
    class Meta:
        model = Stock
        fields = (
            'symbol', 'name', 'exchange', 'sector', 'currency',
            'market_cap', 'is_active'
        )

    def validate_symbol(self, value):
        """Ensure symbol is uppercase."""
        return value.upper()


class StockUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for stock price updates (OHLCV data).
    """
    class Meta:
        model = StockUpdate
        fields = (
            'id', 'timestamp', 'open_price', 'high_price', 'low_price',
            'close_price', 'volume', 'change_percent', 'trend',
            'timeframe', 'data_source', 'ai_analysis', 'created_at'
        )
        read_only_fields = fields


# =============================================================================
# Watchlist Serializers
# =============================================================================

class WatchlistSerializer(serializers.ModelSerializer):
    """
    Serializer for reading watchlist items with nested stock info.
    """
    stock = StockListSerializer(read_only=True)

    class Meta:
        model = UserStockPreference
        fields = (
            'id', 'stock', 'notification_frequency', 'threshold_percent',
            'is_active', 'created_at', 'updated_at'
        )
        read_only_fields = ('id', 'created_at', 'updated_at')


class WatchlistCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for adding stocks to watchlist.
    """
    stock_id = serializers.PrimaryKeyRelatedField(
        queryset=Stock.objects.filter(is_active=True),
        source='stock',
        write_only=True
    )

    class Meta:
        model = UserStockPreference
        fields = ('stock_id', 'notification_frequency', 'threshold_percent')

    def validate(self, attrs):
        """Check if user already has this stock in watchlist."""
        user = self.context['request'].user
        stock = attrs.get('stock')
        
        if UserStockPreference.objects.filter(user=user, stock=stock).exists():
            raise serializers.ValidationError({
                'stock_id': 'This stock is already in your watchlist.'
            })
        return attrs

    def create(self, validated_data):
        """Create watchlist item with current user."""
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class WatchlistUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating watchlist preferences.
    """
    class Meta:
        model = UserStockPreference
        fields = ('notification_frequency', 'threshold_percent', 'is_active')
