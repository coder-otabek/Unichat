from django.urls import path
from . import views
urlpatterns = [
    path('',              views.chat_ask),
    path('sessions/',     views.sessions),
    path('sessions/<int:pk>/', views.session_detail),
]
