from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import *

urlpatterns = [
    # Authentication endpoints
    path('auth/register/', RegisterView.as_view(), name='register'),
    path('auth/login/', CustomTokenObtainPairView.as_view(), name='login'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/logout/', LogoutView.as_view(), name='logout'),
    path('auth/change-password/', ChangePasswordView.as_view(), name='change_password'),
    
    # User profile
    path('auth/profile/', UserProfileView.as_view(), name='user_profile'),
    
    # Stock endpoints
    path('stocks/', StockListView.as_view(), name='stock_list'),
    path('stocks/create/', StockAdminCreateView.as_view(), name='stock_create'),
    path('stocks/<str:symbol>/', StockDetailView.as_view(), name='stock_detail'),
    path('stocks/<str:symbol>/edit/', StockAdminUpdateView.as_view(), name='stock_edit'),
    
    # Watchlist endpoints
    path('watchlist/', WatchlistView.as_view(), name='watchlist'),
    path('watchlist/<int:pk>/', WatchlistDetailView.as_view(), name='watchlist_detail'),
]
