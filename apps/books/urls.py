from django.urls import path
from . import views
urlpatterns = [
    path('',                views.book_list),
    path('upload/',         views.book_upload),
    path('<int:pk>/delete/',views.book_delete),
    path('<int:pk>/reprocess/',views.book_reprocess),
]
