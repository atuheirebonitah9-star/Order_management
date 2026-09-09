from django.urls import path
from . import views

app_name = 'orders'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),  
    path('orders/', views.order_list, name='order_list'),
    path('orders/<int:order_id>/', views.order_detail, name='order_detail'),
    path('customers/', views.customer_list, name='customer_list'),
    path('restaurants/', views.restaurant_list, name='restaurant_list'),
    path('riders/', views.rider_list, name='rider_list'),
    path('menu/', views.menu_list, name='menu_list'),
]