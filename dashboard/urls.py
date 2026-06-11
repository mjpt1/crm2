from django.urls import path
from django.views.generic import RedirectView
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', RedirectView.as_view(pattern_name='dashboard:index'), name='root'),
    path('dashboard/', views.index, name='index'),
]
