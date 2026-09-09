from django.db import models

class Customer(models.Model):
    customer_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20)
    address = models.TextField()
    city = models.CharField(max_length=50, blank=True, null=True)
    parish = models.CharField(max_length=50, blank=True, null=True)
    division = models.CharField(max_length=50, blank=True, null=True)
    registration_date = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'customer'  # Matches your MySQL table name

    def __str__(self):
        return self.name

class Restaurant(models.Model):
    restaurant_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)
    address = models.TextField()
    phone = models.CharField(max_length=20)
    email = models.EmailField(blank=True, null=True)
    cuisine_type = models.CharField(max_length=50, blank=True, null=True)
    is_open = models.BooleanField(default=True)
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.00)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'restaurant'

    def __str__(self):
        return self.name

class DeliveryRider(models.Model):
    RIDER_STATUS = [
        ('available', 'Available'),
        ('busy', 'Busy'),
        ('offline', 'Offline'),
    ]
    
    rider_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=20)
    email = models.EmailField(unique=True, blank=True, null=True)
    status = models.CharField(max_length=20, choices=RIDER_STATUS, default='available')
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.00)
    vehicle_type = models.CharField(max_length=30)
    vehicle_plate = models.CharField(max_length=20)
    total_deliveries = models.IntegerField(default=0)
    hired_date = models.DateField(blank=True, null=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'delivery_rider'

    def __str__(self):
        return self.name

class MenuItem(models.Model):
    item_id = models.AutoField(primary_key=True)
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, db_column='restaurant_id')
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    category = models.CharField(max_length=50, blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    preparation_time = models.IntegerField(default=15)
    is_available = models.BooleanField(default=True)
    calories = models.IntegerField(blank=True, null=True)

    class Meta:
        db_table = 'menu_item'

    def __str__(self):
        return self.name

class Order(models.Model):
    ORDER_STATUS = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('preparing', 'Preparing'),
        ('ready', 'Ready'),
        ('delivering', 'Delivering'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    ]
    
    DELIVERY_STATUS = [
        ('pending', 'Pending'),
        ('picked_up', 'Picked Up'),
        ('in_transit', 'In Transit'),
        ('delivered', 'Delivered'),
    ]
    
    PAYMENT_STATUS = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('failed', 'Failed'),
    ]
    
    PAYMENT_METHOD = [
        ('cash', 'Cash'),
        ('card', 'Card'),
        ('mobile_money', 'Mobile Money'),
    ]
    
    order_id = models.AutoField(primary_key=True)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, db_column='customer_id')
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, db_column='restaurant_id')
    rider = models.ForeignKey(DeliveryRider, on_delete=models.SET_NULL, null=True, blank=True, db_column='rider_id')
    status = models.CharField(max_length=20, choices=ORDER_STATUS, default='pending')
    total = models.DecimalField(max_digits=10, decimal_places=2)
    delivery_status = models.CharField(max_length=20, choices=DELIVERY_STATUS, default='pending')
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS, default='pending')
    placed_at = models.DateTimeField(auto_now_add=True)
    delivery_address = models.TextField()
    special_instructions = models.TextField(blank=True, null=True)
    delivery_fee = models.DecimalField(max_digits=10, decimal_places=2, default=5000.00)
    estimated_delivery_time = models.DateTimeField(blank=True, null=True)
    actual_delivery_time = models.DateTimeField(blank=True, null=True)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD, default='mobile_money')

    class Meta:
        db_table = 'orders'

    def __str__(self):
        return f"Order #{self.order_id} - {self.customer.name}"

class OrderItem(models.Model):
    item_id = models.AutoField(primary_key=True)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, db_column='order_id')
    menu_item = models.ForeignKey(MenuItem, on_delete=models.CASCADE, db_column='menu_item_id')
    quantity = models.IntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    special_instructions = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'order_item'

    def __str__(self):
        return f"{self.menu_item.name} x{self.quantity}"