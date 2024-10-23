from django.urls import path
from . import views

urlpatterns = [
    path('html_coding/', views.html_upload_and_prepare, name='html_upload_and_prepare'),
]
