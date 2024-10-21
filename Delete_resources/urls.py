from django.urls import path
from . import views


urlpatterns = [
    path('delete_resources', views.delete_resources_view, name='delete_resources'),
    path('submit-request/', views.submit_request, name='submit_request'),
    path('task-details/<str:request_id>/', views.get_task_details, name='task_details'),
]
