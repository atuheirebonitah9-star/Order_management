from django.urls import path
from . import views

app_name = 'orders'

urlpatterns = [
    # Dashboard
    path('', views.dashboard, name='dashboard'),  
    
    # Orders
    path('orders/', views.order_list, name='order_list'),
    path('orders/create/', views.order_create, name='order_create'),
    path('orders/<str:order_id>/', views.order_detail, name='order_detail'),
    path('orders/<str:order_id>/edit/', views.order_update, name='order_update'),
    path('orders/<str:order_id>/delete/', views.order_delete, name='order_delete'),
    
    # Order Items (For adding/removing items from an order)
    path('order-items/<int:pk>/delete/', views.orderitem_delete, name='orderitem_delete'),
    
    # Customers
    path('customers/', views.customer_list, name='customer_list'),
    path('customers/create/', views.customer_create, name='customer_create'),
    path('customers/<str:pk>/edit/', views.customer_update, name='customer_update'),
    path('customers/<str:pk>/delete/', views.customer_delete, name='customer_delete'),
    
    # Restaurants
    path('restaurants/', views.restaurant_list, name='restaurant_list'),
    path('restaurants/create/', views.restaurant_create, name='restaurant_create'),
    
    # Riders
    path('riders/', views.rider_list, name='rider_list'),
    path('riders/create/', views.rider_create, name='rider_create'),
    
    # Menu Items
    path('menu/', views.menu_list, name='menu_list'),
    path('menu/create/', views.menu_item_create, name='menu_item_create'),

    # Reports (staff only)
    path('reports/', views.reports, name='reports'),
]