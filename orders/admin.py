from django.contrib import admin
from .models import Customer, Restaurant, DeliveryRider, MenuItem, Order, OrderItem, Payment, Review


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('customer_id', 'customer_name', 'phone_contact', 'email_address')
    search_fields = ('customer_name', 'phone_contact')


@admin.register(Restaurant)
class RestaurantAdmin(admin.ModelAdmin):
    list_display = ('restaurant_id', 'name', 'address', 'is_open')
    list_filter = ('is_open',)
    search_fields = ('name',)


@admin.register(DeliveryRider)
class DeliveryRiderAdmin(admin.ModelAdmin):
    list_display = ('rider_id', 'name', 'status', 'rating')
    list_filter = ('status',)
    search_fields = ('name',)


@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    list_display = ('item_id', 'name', 'restaurant', 'category', 'price', 'is_available')
    list_filter = ('category', 'is_available')
    search_fields = ('name',)


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('order_id', 'customer', 'restaurant', 'rider', 'status', 'delivery_status', 'payment_status', 'total')
    list_filter = ('status', 'delivery_status', 'payment_status')


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('order', 'menu_item', 'quantity', 'unit_price')


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('payment_id', 'order', 'amount', 'method', 'status', 'paid_at')
    list_filter = ('method', 'status')


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('review_id', 'order', 'customer', 'restaurant_rating', 'rider_rating')