from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from . import views

urlpatterns = [
    path('register/', views.register),
    path('login/',    views.login),
    path('google/',   views.google_login),
    path('logout/',   views.logout_view),
    path('me/',       views.me),
    path('refresh/',  TokenRefreshView.as_view()),
]
