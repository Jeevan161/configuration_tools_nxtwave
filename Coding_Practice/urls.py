from django.urls import path
from . import views

urlpatterns = [
    path('Coding_Practice', views.upload_and_prepare, name='upload_and_prepare'),
]
