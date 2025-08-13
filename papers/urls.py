from django.urls import path
from . import views

urlpatterns = [
    path('api/papers/<str:subject>/<int:year>/', views.get_papers, name='get_papers'),
]