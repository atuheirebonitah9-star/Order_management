from django.contrib import admin
from .models import Customer, Restaurant, DeliveryRider, MenuItem, Order, OrderItem

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('customer_id', 'name', 'email', 'phone', 'city', 'registration_date')
    search_fields = ('name', 'email', 'phone')
    list_filter = ('city', 'is_active')

@admin.register(Restaurant)
class RestaurantAdmin(admin.ModelAdmin):
    list_display = ('restaurant_id', 'name', 'cuisine_type', 'is_open', 'rating')
    search_fields = ('name', 'cuisine_type')
    list_filter = ('is_open', 'cuisine_type')

@admin.register(DeliveryRider)
class DeliveryRiderAdmin(admin.ModelAdmin):
    list_display = ('rider_id', 'name', 'status', 'rating', 'total_deliveries')
    search_fields = ('name', 'phone', 'vehicle_plate')
    list_filter = ('status', 'vehicle_type', 'is_active')

@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    list_display = ('item_id', 'name', 'restaurant', 'price', 'is_available', 'category')
    search_fields = ('name', 'category')
    list_filter = ('restaurant', 'is_available', 'category')

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('order_id', 'customer', 'restaurant', 'rider', 'status', 'total', 'payment_status')
    search_fields = ('customer__name', 'restaurant__name', 'delivery_address')
    list_filter = ('status', 'payment_status', 'payment_method', 'placed_at')

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('item_id', 'order', 'menu_item', 'quantity', 'unit_price')
    search_fields = ('order__order_id', 'menu_item__name')