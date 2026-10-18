from django import forms
from .models import (
    Customer, Restaurant, DeliveryRider, 
    MenuItem, Order, OrderItem
)

class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        exclude = ['customer_id']
        widgets = {
            'customer_name': forms.TextInput(attrs={'class': 'form-control'}),
            'phone_contact': forms.TextInput(attrs={'class': 'form-control'}),
            'email_address': forms.EmailInput(attrs={'class': 'form-control'}),
        }

class RestaurantForm(forms.ModelForm):
    class Meta:
        model = Restaurant
        exclude = ['restaurant_id']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.TextInput(attrs={'class': 'form-control'}),
            'is_open': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class DeliveryRiderForm(forms.ModelForm):
    class Meta:
        model = DeliveryRider
        exclude = ['rider_id']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'rating': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1'}),
        }

class MenuItemForm(forms.ModelForm):
    class Meta:
        model = MenuItem
        exclude = ['item_id']
        widgets = {
            'restaurant': forms.Select(attrs={'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'category': forms.TextInput(attrs={'class': 'form-control'}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'is_available': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class OrderForm(forms.ModelForm):
    # Customer details typed directly into the order form
    customer_name = forms.CharField(
        max_length=20,
        label="Customer Name",
        widget=forms.TextInput(attrs={'class': 'form-control', 'list': 'customer-list', 'autocomplete': 'off'})
    )
    phone_contact = forms.CharField(
        max_length=10,
        label="Phone Number",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. 0712345678'})
    )
    email_address = forms.EmailField(
        required=False,
        label="Email Address (Optional)",
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )

    class Meta:
        model = Order
        # Exclude all admin fields for now (they will be added back on Edit)
        exclude = [
            'order_id', 'placed_at', 'customer', 'total', 
            'rider', 'status', 'delivery_status', 'payment_status'
        ]
        widgets = {
            'restaurant': forms.Select(attrs={'class': 'form-control'}),
            'delivery_address': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # If editing an EXISTING order, add the admin fields back in
        if self.instance and self.instance.pk:
            # Pre-fill customer info
            self.fields['customer_name'].initial = self.instance.customer.customer_name
            self.fields['phone_contact'].initial = self.instance.customer.phone_contact
            self.fields['email_address'].initial = self.instance.customer.email_address
            
            # Add Admin fields for logistics management
            self.fields['rider'] = forms.ModelChoiceField(
                queryset=DeliveryRider.objects.all(), 
                required=False, 
                widget=forms.Select(attrs={'class': 'form-control'})
            )
            self.fields['status'] = forms.ChoiceField(
                choices=Order.ORDER_STATUS, 
                widget=forms.Select(attrs={'class': 'form-control'})
            )
            self.fields['delivery_status'] = forms.ChoiceField(
                choices=Order.DELIVERY_STATUS, 
                widget=forms.Select(attrs={'class': 'form-control'})
            )
            self.fields['payment_status'] = forms.ChoiceField(
                choices=Order.PAYMENT_STATUS, 
                widget=forms.Select(attrs={'class': 'form-control'})
            )

class OrderItemForm(forms.ModelForm):
    class Meta:
        model = OrderItem
        fields = ['menu_item', 'quantity']
        widgets = {
            'menu_item': forms.Select(attrs={'class': 'form-control'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': '1', 'value': '1'}),
        }