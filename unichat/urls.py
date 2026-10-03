from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

admin.site.site_header = f'{settings.SITE_TITLE} Admin'
admin.site.site_title  =  settings.SITE_TITLE
admin.site.index_title = 'Boshqaruv paneli'

urlpatterns = [
    path('admin/',       admin.site.urls),
    path('',             include('apps.core.urls')),
    path('api/auth/',    include('apps.accounts.urls')),
    path('api/books/',   include('apps.books.urls')),
    path('api/chat/',    include('apps.chat.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
