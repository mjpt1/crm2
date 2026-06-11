from django.urls import path
from . import views

app_name = 'invoices'

urlpatterns = [
    path('', views.invoice_list, name='list'),
    path('create/', views.invoice_create, name='create'),
    path('<int:pk>/', views.invoice_detail, name='detail'),
    path('<int:pk>/approve/', views.invoice_approve, name='approve'),
    path('<int:pk>/cancel/', views.invoice_cancel, name='cancel'),
    path('<int:pk>/send-link/', views.send_payment_link, name='send_link'),
    path('payment/callback/', views.payment_callback, name='callback'),
    path('payment/webhook/', views.zibal_webhook, name='webhook'),
]
