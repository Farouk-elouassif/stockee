from rest_framework import generics, status, filters
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from .serializers import *
from .models import UserProfile, Stock, UserStockPreference
from .permissions import IsAdminRole, IsOwner, IsAdminOrReadOnly


class RegisterView(generics.CreateAPIView):
    """
    API endpoint for user registration.
    Returns JWT tokens upon successful registration.
    """
    queryset = User.objects.all()
    permission_classes = (AllowAny,)
    serializer_class = RegisterSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        # Generate JWT tokens for the new user
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'profile': {
                    'role': user.profile.role,
                    'timezone': user.profile.timezone,
                    'email_notifications': user.profile.email_notifications,
                }
            },
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            },
            'message': 'User registered successfully'
        }, status=status.HTTP_201_CREATED)


class CustomTokenObtainPairView(TokenObtainPairView):
    """
    Custom login view that returns user info along with tokens.
    """
    serializer_class = CustomTokenObtainPairSerializer


class UserProfileView(generics.RetrieveUpdateAPIView):
    """
    API endpoint to get and update current user's profile.
    GET: Retrieve profile
    PATCH/PUT: Update profile
    """
    permission_classes = (IsAuthenticated,)

    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return UserUpdateSerializer
        return UserSerializer

    def get_object(self):
        return self.request.user


class ChangePasswordView(APIView):
    """
    API endpoint for changing password.
    """
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        
        # Set new password
        request.user.set_password(serializer.validated_data['new_password'])
        request.user.save()
        
        return Response({
            'message': 'Password changed successfully'
        }, status=status.HTTP_200_OK)


class LogoutView(APIView):
    """
    API endpoint for logging out (blacklisting refresh token).
    """
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        try:
            refresh_token = request.data.get('refresh')
            if not refresh_token:
                return Response({
                    'error': 'Refresh token is required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            token = RefreshToken(refresh_token)
            token.blacklist()
            
            return Response({
                'message': 'Successfully logged out'
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'error': 'Invalid token'
            }, status=status.HTTP_400_BAD_REQUEST)


# =============================================================================
# Stock Views
# =============================================================================

class StockListView(generics.ListAPIView):
    """
    List all stocks with search and filtering.
    Public endpoint - no authentication required.
    
    Query params:
    - search: Search by symbol or name
    - exchange: Filter by exchange (e.g., NASDAQ)
    - sector: Filter by sector (e.g., Technology)
    - is_active: Filter active/inactive (true/false)
    - ordering: Sort by field (e.g., -last_price, symbol)
    """
    queryset = Stock.objects.filter(is_active=True)
    serializer_class = StockListSerializer
    permission_classes = (AllowAny,)
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['symbol', 'name']
    ordering_fields = ['symbol', 'name', 'last_price', 'sector', 'exchange', 'created_at']
    ordering = ['symbol']

    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by exchange
        exchange = self.request.query_params.get('exchange')
        if exchange:
            queryset = queryset.filter(exchange__iexact=exchange)
        
        # Filter by sector
        sector = self.request.query_params.get('sector')
        if sector:
            queryset = queryset.filter(sector__icontains=sector)
        
        # Filter by is_active (allow viewing inactive for admins)
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            if is_active.lower() == 'false':
                queryset = Stock.objects.filter(is_active=False)
            elif is_active.lower() == 'all':
                queryset = Stock.objects.all()
        
        return queryset


class StockDetailView(generics.RetrieveAPIView):
    """
    Get stock detail by symbol with recent price updates.
    Public endpoint - no authentication required.
    """
    serializer_class = StockDetailSerializer
    permission_classes = (AllowAny,)
    lookup_field = 'symbol'
    lookup_url_kwarg = 'symbol'

    def get_queryset(self):
        return Stock.objects.all()

    def get_object(self):
        symbol = self.kwargs.get('symbol').upper()
        return get_object_or_404(Stock, symbol=symbol)


class StockAdminCreateView(generics.CreateAPIView):
    """
    Create a new stock (admin only).
    """
    queryset = Stock.objects.all()
    serializer_class = StockCreateSerializer
    permission_classes = (IsAuthenticated, IsAdminRole)


class StockAdminUpdateView(generics.RetrieveUpdateDestroyAPIView):
    """
    Update or delete a stock (admin only).
    """
    serializer_class = StockCreateSerializer
    permission_classes = (IsAuthenticated, IsAdminRole)
    lookup_field = 'symbol'
    lookup_url_kwarg = 'symbol'

    def get_object(self):
        symbol = self.kwargs.get('symbol').upper()
        return get_object_or_404(Stock, symbol=symbol)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        # Soft delete - just mark as inactive
        instance.is_active = False
        instance.save()
        return Response({
            'message': f'Stock {instance.symbol} has been deactivated'
        }, status=status.HTTP_200_OK)


# =============================================================================
# Watchlist Views
# =============================================================================

class WatchlistView(generics.ListCreateAPIView):
    """
    List user's watchlist or add a new stock to watchlist.
    
    GET: List all stocks in user's watchlist
    POST: Add a stock to watchlist
    """
    permission_classes = (IsAuthenticated,)

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return WatchlistCreateSerializer
        return WatchlistSerializer

    def get_queryset(self):
        return UserStockPreference.objects.filter(
            user=self.request.user
        ).select_related('stock')


class WatchlistDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Get, update, or remove a stock from watchlist.
    
    GET: Get watchlist item details
    PATCH/PUT: Update notification preferences
    DELETE: Remove from watchlist
    """
    permission_classes = (IsAuthenticated, IsOwner)

    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return WatchlistUpdateSerializer
        return WatchlistSerializer

    def get_queryset(self):
        return UserStockPreference.objects.filter(
            user=self.request.user
        ).select_related('stock')

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        stock_symbol = instance.stock.symbol
        instance.delete()
        return Response({
            'message': f'{stock_symbol} removed from watchlist'
        }, status=status.HTTP_200_OK)
