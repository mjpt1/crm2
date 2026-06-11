from django.urls import path
from . import views

app_name = 'leads'

urlpatterns = [
    path('', views.lead_list, name='list'),
    path('create/', views.lead_create, name='create'),
    path('<int:pk>/', views.lead_detail, name='detail'),
    path('<int:pk>/edit/', views.lead_edit, name='edit'),
    path('<int:pk>/assign/', views.lead_assign, name='assign'),
    path('<int:pk>/auto-assign/', views.lead_auto_assign, name='auto_assign'),
    path('capture/<uuid:token>/', views.capture_lead, name='capture'),
    path('utm/', views.utm_list, name='utm_list'),
    path('utm/create/', views.utm_create, name='utm_create'),
]
