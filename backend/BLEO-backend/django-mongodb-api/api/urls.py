from django.urls import path
from api.Views.User.UserView import UserListCreateView, UserDetailView
from api.Views.Link.LinkView import LinkListCreateView, LinkDetailView
from api.Views.MessageDay.MessageDayView import MessageDayListCreateView, MessageDayDetailView, MoodOptionsView
from api.Views.MessageDay.MessageDayView import MessageDayCreateView
from api.Views.MessageDay.Message.MessageView import MessageOperationsView

urlpatterns = [
    # User CRUD endpoints
    path('users/', UserListCreateView.as_view(), name='user-list-create'),
    path('users/<int:bleoid>/', UserDetailView.as_view(), name='user-detail'),

    # Link CRUD endpoints
    path('links/', LinkListCreateView.as_view(), name='link-list-create'),
    path('links/<int:bleoidPartner1>/', LinkDetailView.as_view(), name='link-detail'),
    
    # MessageDay CRUD endpoints - COLLECTION LEVEL
    path('messagedays/', MessageDayListCreateView.as_view(), name='message-day-list'),
    path('messagedays/<int:bleoid>/', MessageDayCreateView.as_view(), name='message-day-create-with-id'),
    # MessageDay CRUD endpoints - INDIVIDUAL RESOURCE LEVEL
    path('messagedays/<int:bleoid>/<str:date>/', MessageDayDetailView.as_view(), name='message-day-detail'),
    
    # Mood options endpoint
    path('mood-options/', MoodOptionsView.as_view(), name='mood-options'),

    # Message operations
    # Message operations - GET all messages for user
    path('messagedays/<int:bleoid>/messages/', MessageOperationsView.as_view(), name='user-messages'),
    # Message operations - GET/POST/PUT/DELETE messages for a specific date
    path('messagedays/<int:bleoid>/<str:date>/messages/', MessageOperationsView.as_view(), name='message-operations'),
    # Message operations - GET/PUT/DELETE a specific message
    path('messagedays/<int:bleoid>/<str:date>/messages/<int:message_id>/', MessageOperationsView.as_view(), name='message-detail'),
    ]