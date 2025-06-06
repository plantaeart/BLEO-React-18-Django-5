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
from api.Views.DebugLogs.DebugLogViews import LoggingView, AdminLogsView, AdminLogDetailView
from api.Views.AppParameters.AppParametersView import AppParametersView, AppParameterDetailView

urlpatterns = [
    # User CRUD endpoints
    path('users/', UserListCreateView.as_view(), name='user-list-create'),
    path('users/<str:bleoid>/', UserDetailView.as_view(), name='user-detail'),  

    # Link CRUD endpoints
    path('links/', LinkListCreateView.as_view(), name='link-list-create'),
    path('links/<str:bleoid>/', LinkDetailView.as_view(), name='link-detail'),  
    
    # MessagesDays CRUD endpoints - COLLECTION LEVEL
    path('messagesdays/', MessageDayListCreateView.as_view(), name='message-day-list'),
    path('messagesdays/<str:bleoid>/', MessageDayCreateView.as_view(), name='message-day-create-with-id'),  
    # MessagesDays CRUD endpoints - INDIVIDUAL RESOURCE LEVEL
    path('messagesdays/<str:bleoid>/<str:date>/', MessageDayDetailView.as_view(), name='message-day-detail'),  
    
    # Mood options endpoint
    path('mood-options/', MoodOptionsView.as_view(), name='mood-options'),

    # Message operations
    # Message operations - GET all messages for user
    path('messagesdays/<str:bleoid>/messages/', MessageOperationsView.as_view(), name='user-messages'),  
    # Message operations - GET/POST/PUT/DELETE messages for a specific date
    path('messagesdays/<str:bleoid>/<str:date>/messages/', MessageOperationsView.as_view(), name='message-operations'),  
    # Message operations - GET/PUT/DELETE a specific message
    path('messagesdays/<str:bleoid>/<str:date>/messages/<int:message_id>/', MessageOperationsView.as_view(), name='message-detail'), 
    ]

urlpatterns += [
    # Authentication
    path('auth/login/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/logout/', LogoutView.as_view(), name='auth_logout'),
    
    # Token validation
    path('auth/validate-token/', TokenValidationView.as_view(), name='validate_token'),

    # Password management
    path('auth/password-reset/request/', PasswordResetRequestView.as_view(), name='password-reset-request'),
    path('auth/password-reset/confirm/', PasswordResetConfirmView.as_view(), name='password-reset-confirm'),
    
    # Email verification
    path('auth/email/verify/', EmailVerificationView.as_view(), name='email-verification'),
    
    # User connections
    path('connections/request/', ConnectionRequestView.as_view(), name='connection_request'),
    path('connections/<str:connection_id>/', ConnectionResponseView.as_view(), name='connection_response'),
    path('connections/', ConnectionListView.as_view(), name='connection_list'),
]

urlpatterns += [
    # Client-side logging endpoint
    path('logs/', LoggingView.as_view(), name='logs'),
    
    # Admin endpoints
    path('logs/admin/', AdminLogsView.as_view(), name='admin-logs'),
    path('logs/admin/<str:log_id>/', AdminLogDetailView.as_view(), name='admin-log-detail'),
]

urlpatterns += [
    # App Parameters endpoints
    path('app-parameters/', AppParametersView.as_view(), name='app-parameters'),
    path('app-parameters/<str:param_name>/', AppParameterDetailView.as_view(), name='app-parameter-detail'),
]