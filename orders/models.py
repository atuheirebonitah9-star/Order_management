from django.db import models
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .utils import generate_id


class Customer(models.Model):
    customer_id = models.CharField(max_length=8, primary_key=True, editable=False)
    customer_name = models.CharField(max_length=20)
    phone_contact = models.CharField(max_length=10)
    email_address = models.EmailField(max_length=30, blank=True, null=True)

    class Meta:
        db_table = 'customer'

    def save(self, *args, **kwargs):
        if not self.customer_id:
            self.customer_id = generate_id(Customer, 'customer_id', 'CUS')
        super().save(*args, **kwargs)

    def __str__(self):
        return self.customer_name


class Restaurant(models.Model):
    restaurant_id = models.CharField(max_length=8, primary_key=True, editable=False)
    name = models.CharField(max_length=30)
    address = models.CharField(max_length=50)
    is_open = models.BooleanField(default=True)

    class Meta:
        db_table = 'restaurant'

    def save(self, *args, **kwargs):
        if not self.restaurant_id:
            self.restaurant_id = generate_id(Restaurant, 'restaurant_id', 'RES')
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class DeliveryRider(models.Model):
    RIDER_STATUS = [
        ('available', 'Available'),
        ('busy', 'Busy'),
        ('offline', 'Offline'),
    ]

    rider_id = models.CharField(max_length=8, primary_key=True, editable=False)
    name = models.CharField(max_length=20)
    status = models.CharField(max_length=15, choices=RIDER_STATUS, default='available')
    rating = models.DecimalField(max_digits=2, decimal_places=1, default=0.0)

    class Meta:
        db_table = 'delivery_rider'

    def save(self, *args, **kwargs):
        if not self.rider_id:
            self.rider_id = generate_id(DeliveryRider, 'rider_id', 'RID')
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class MenuItem(models.Model):
    item_id = models.CharField(max_length=8, primary_key=True, editable=False)
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, db_column='restaurant_id')
    name = models.CharField(max_length=30)
    category = models.CharField(max_length=20)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    is_available = models.BooleanField(default=True)

    class Meta:
        db_table = 'menu_item'

    def save(self, *args, **kwargs):
        if not self.item_id:
            self.item_id = generate_id(MenuItem, 'item_id', 'ITM')
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Order(models.Model):
    ORDER_STATUS = [
        ('pending', 'Pending'),
        ('preparing', 'Preparing'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    DELIVERY_STATUS = [
        ('not_started', 'Not Started'),
        ('in_transit', 'In Transit'),
        ('delivered', 'Delivered'),
    ]
    PAYMENT_STATUS = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('failed', 'Failed'),
    ]

    order_id = models.CharField(max_length=8, primary_key=True, editable=False)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, db_column='customer_id')
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, db_column='restaurant_id')
    rider = models.ForeignKey(DeliveryRider, on_delete=models.SET_NULL, null=True, blank=True, db_column='rider_id')
    status = models.CharField(max_length=15, choices=ORDER_STATUS, default='pending')
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    delivery_status = models.CharField(max_length=15, choices=DELIVERY_STATUS, default='not_started')
    payment_status = models.CharField(max_length=15, choices=PAYMENT_STATUS, default='pending')
    placed_at = models.DateTimeField(auto_now_add=True)
    delivery_address = models.CharField(max_length=100)

    class Meta:
        db_table = 'orders'

    def save(self, *args, **kwargs):
        if not self.order_id:
            self.order_id = generate_id(Order, 'order_id', 'ORD')
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Order {self.order_id} - {self.customer.customer_name}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, db_column='order_id')
    menu_item = models.ForeignKey(MenuItem, on_delete=models.CASCADE, db_column='item_id')
    quantity = models.IntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        db_table = 'order_item'
        unique_together = ('order', 'menu_item')

    def __str__(self):
        return f"{self.menu_item.name} x{self.quantity}"

    @property
    def get_subtotal(self):
        return self.quantity * self.unit_price


class Payment(models.Model):
    PAYMENT_METHOD = [
        ('cash', 'Cash'),
        ('mobile_banking', 'Mobile Banking'),
        ('mobile_money', 'Mobile Money'),
    ]
    PAYMENT_STATUS = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]

    payment_id = models.CharField(max_length=8, primary_key=True, editable=False)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, db_column='order_id')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    method = models.CharField(max_length=15, choices=PAYMENT_METHOD)
    status = models.CharField(max_length=15, choices=PAYMENT_STATUS, default='pending')
    transaction_id = models.CharField(max_length=20)
    paid_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = 'payment'

    def save(self, *args, **kwargs):
        if not self.payment_id:
            self.payment_id = generate_id(Payment, 'payment_id', 'PAY')
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Payment {self.payment_id} for {self.order_id}"


class Review(models.Model):
    review_id = models.CharField(max_length=8, primary_key=True, editable=False)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, db_column='order_id')
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, db_column='customer_id')
    rider_rating = models.DecimalField(max_digits=2, decimal_places=1, blank=True, null=True)
    restaurant_rating = models.DecimalField(max_digits=2, decimal_places=1, blank=True, null=True)
    comment = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        db_table = 'review'

    def save(self, *args, **kwargs):
        if not self.review_id:
            self.review_id = generate_id(Review, 'review_id', 'REV')
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Review {self.review_id} for {self.order_id}"


# ==========================================
# AUTOMATIC TOTAL CALCULATION SIGNALS
# ==========================================
@receiver([post_save, post_delete], sender=OrderItem)
def update_order_total(sender, instance, **kwargs):
    """Recalculates the order total whenever an item is added, updated, or deleted.

    Queries the database fresh (ignoring any prefetched/cached items) and
    updates only the total column, so it never overwrites other order fields.
    """
    items = OrderItem.objects.filter(order_id=instance.order_id)
    total = sum(i.quantity * i.unit_price for i in items)
    Order.objects.filter(pk=instance.order_id).update(total=total)