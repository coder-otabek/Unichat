from django.urls import path
from . import views
from .avatar_proxy import avatar_proxy

urlpatterns = [
    path('',          views.index),
    path('panel/',    views.panel),
    path('avatar/',   avatar_proxy),
    path('logo/',     views.site_logo),
    path('api/config/',                           views.public_config),
    path('api/panel/stats/',                      views.panel_stats),
    path('api/panel/users/',                      views.panel_users),
    path('api/panel/users/<int:pk>/toggle/',      views.toggle_user),
    path('api/panel/web-search/toggle/',          views.toggle_web_search),
    path('api/panel/web-search/settings/',        views.update_web_search_settings),
    path('api/panel/rate-limit/toggle/',          views.toggle_rate_limit),
    path('api/panel/rate-limit/settings/',        views.update_rate_limit_settings),
]