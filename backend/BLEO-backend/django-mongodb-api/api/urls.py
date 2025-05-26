from django.urls import path
from api.Views.User.UserView import UserListCreateView, UserDetailView
from api.Views.Link.LinkView import LinkListCreateView, LinkDetailView
from api.Views.MessagesDays.MessagesDaysView import MessageDayListCreateView, MessageDayDetailView, MoodOptionsView
from api.Views.MessagesDays.MessagesDaysView import MessageDayCreateView
from api.Views.MessagesDays.Message.MessageView import MessageOperationsView
from auth.jwt_auth import CustomTokenObtainPairView
from rest_framework_simplejwt.views import TokenRefreshView
from auth.logout import LogoutView
from auth.password_reset import PasswordResetRequestView, PasswordResetConfirmView
from auth.email_verification import EmailVerificationView
from auth.connection import ConnectionRequestView, ConnectionResponseView, ConnectionListView
from auth.token_validation import TokenValidationView

urlpatterns = [
    # User CRUD endpoints
    path('users/', UserListCreateView.as_view(), name='user-list-create'),
    path('users/<str:bleoid>/', UserDetailView.as_view(), name='user-detail'),  # Changed from int to str

    # Link CRUD endpoints
    path('links/', LinkListCreateView.as_view(), name='link-list-create'),
    path('links/<str:bleoidPartner1>/', LinkDetailView.as_view(), name='link-detail'),  # Changed from int to str
    
    # MessagesDays CRUD endpoints - COLLECTION LEVEL
    path('messagesdays/', MessageDayListCreateView.as_view(), name='message-day-list'),
    path('messagesdays/<str:bleoid>/', MessageDayCreateView.as_view(), name='message-day-create-with-id'),  # Changed from int to str
    # MessagesDays CRUD endpoints - INDIVIDUAL RESOURCE LEVEL
    path('messagesdays/<str:bleoid>/<str:date>/', MessageDayDetailView.as_view(), name='message-day-detail'),  # Changed from int to str
    
    # Mood options endpoint
    path('mood-options/', MoodOptionsView.as_view(), name='mood-options'),

    # Message operations
    # Message operations - GET all messages for user
    path('messagesdays/<str:bleoid>/messages/', MessageOperationsView.as_view(), name='user-messages'),  # Changed from int to str
    # Message operations - GET/POST/PUT/DELETE messages for a specific date
    path('messagesdays/<str:bleoid>/<str:date>/messages/', MessageOperationsView.as_view(), name='message-operations'),  # Changed from int to str
    # Message operations - GET/PUT/DELETE a specific message
    path('messagesdays/<str:bleoid>/<str:date>/messages/<int:message_id>/', MessageOperationsView.as_view(), name='message-detail'),  # Changed bleoid from int to str
    ]

urlpatterns += [
    # Authentication
    path('auth/login/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/logout/', LogoutView.as_view(), name='auth_logout'),
    
    # Token validation
    path('auth/validate-token/', TokenValidationView.as_view(), name='validate_token'),

    # Password management
    path('auth/password/reset-request/', PasswordResetRequestView.as_view(), name='password_reset_request'),
    path('auth/password/reset-confirm/', PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    
    # Email verification
    path('auth/email/verify-request/', EmailVerificationView.as_view(), name='email_verify_request'),
    path('auth/email/verify-confirm/', EmailVerificationView.as_view(), name='email_verify_confirm'),
    
    # User connections
    path('connections/request/', ConnectionRequestView.as_view(), name='connection_request'),
    path('connections/<str:connection_id>/', ConnectionResponseView.as_view(), name='connection_response'),
    path('connections/', ConnectionListView.as_view(), name='connection_list'),
]