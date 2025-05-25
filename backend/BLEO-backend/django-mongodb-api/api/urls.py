from django.urls import path
from api.Views.User.UserView import UserListCreateView, UserDetailView
from api.Views.Link.LinkView import LinkListCreateView, LinkDetailView

urlpatterns = [
    # User CRUD endpoints
    path('users/', UserListCreateView.as_view(), name='user-list-create'),
    path('users/<int:bleoid>/', UserDetailView.as_view(), name='user-detail'),

    # Link CRUD endpoints
    path('links/', LinkListCreateView.as_view(), name='link-list-create'),
    path('links/<int:bleoidPartner1>/', LinkDetailView.as_view(), name='link-detail'),]