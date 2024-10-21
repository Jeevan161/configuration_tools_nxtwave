from django.urls import path
from . import views

urlpatterns = [
    path('upload/', views.upload_and_merge_zips, name='upload_and_merge_zips'),
    path('rename-json/', views.upload_and_rename_jsons, name='rename_jsons'),  # New tool to rename JSON files
]
