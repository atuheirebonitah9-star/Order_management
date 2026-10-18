from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Count, Sum, Avg, Q
from django.contrib import messages
from django.utils import timezone
from datetime import datetime, timedelta
from .models import Order, Customer, Restaurant, DeliveryRider, MenuItem, OrderItem
from .forms import (
    CustomerForm, RestaurantForm, DeliveryRiderForm, 
    MenuItemForm, OrderForm, OrderItemForm
)

def dashboard(request):
    today = timezone.now().date()
    start_of_day = timezone.make_aware(datetime.combine(today, datetime.min.time()))
    
    total_orders = Order.objects.count()
    pending_orders = Order.objects.filter(status='pending').count()
    delivered_orders = Order.objects.filter(delivery_status='delivered').count()
    today_orders = Order.objects.filter(placed_at__gte=start_of_day).count()
    
    total_customers = Customer.objects.count()
    total_restaurants = Restaurant.objects.filter(is_open=True).count()
    available_riders = DeliveryRider.objects.filter(status='available').count()
    
    total_revenue = Order.objects.filter(status='completed').aggregate(Sum('total'))['total__sum'] or 0
    today_revenue = Order.objects.filter(
        status='completed',
        placed_at__gte=start_of_day
    ).aggregate(Sum('total'))['total__sum'] or 0
    
    recent_orders = Order.objects.select_related('customer', 'restaurant', 'rider').order_by('-placed_at')[:10]
    top_customers = Customer.objects.annotate(order_count=Count('order'), total_spent=Sum('order__total')).filter(order_count__gt=0).order_by('-total_spent')[:5]
    top_restaurants = Restaurant.objects.annotate(order_count=Count('order'), total_revenue=Sum('order__total')).filter(order_count__gt=0).order_by('-order_count')[:5]
    popular_items = MenuItem.objects.annotate(order_count=Count('orderitem')).filter(order_count__gt=0).order_by('-order_count')[:10]
    
    context = {
        'total_orders': total_orders, 'pending_orders': pending_orders, 'delivered_orders': delivered_orders,
        'today_orders': today_orders, 'total_customers': total_customers, 'total_restaurants': total_restaurants,
        'available_riders': available_riders, 'total_revenue': total_revenue, 'today_revenue': today_revenue,
        'recent_orders': recent_orders, 'top_customers': top_customers, 'top_restaurants': top_restaurants,
        'popular_items': popular_items,
    }
    return render(request, 'orders/dashboard.html', context)


def order_list(request):
    orders = Order.objects.select_related('customer', 'restaurant', 'rider').all().order_by('-placed_at')
    status_filter = request.GET.get('status')
    if status_filter:
        orders = orders.filter(status=status_filter)
    
    search_query = request.GET.get('search')
    if search_query:
        orders = orders.filter(
            Q(customer__customer_name__icontains=search_query) |
            Q(restaurant__name__icontains=search_query) |
            Q(delivery_address__icontains=search_query)
        )
    
    statuses = [('pending', 'Pending'), ('preparing', 'Preparing'), ('completed', 'Completed'), ('cancelled', 'Cancelled')]
    context = {'orders': orders, 'statuses': statuses, 'current_status': status_filter, 'search_query': search_query}
    return render(request, 'orders/order_list.html', context)


def order_detail(request, order_id):
    order = get_object_or_404(
        Order.objects.select_related('customer', 'restaurant', 'rider').prefetch_related('orderitem_set__menu_item'),
        order_id=order_id
    )
    
    if request.method == 'POST':
        item_form = OrderItemForm(request.POST)
        if item_form.is_valid():
            order_item = item_form.save(commit=False)
            order_item.order = order
            order_item.unit_price = order_item.menu_item.price
            order_item.save() # The signal in models.py handles the total calculation!

            messages.success(request, f'Added {order_item.menu_item.name} to the order.')
            return redirect('orders:order_detail', order_id=order.order_id)
    else:
        item_form = OrderItemForm()
        item_form.fields['menu_item'].queryset = MenuItem.objects.filter(restaurant=order.restaurant, is_available=True)
    
    context = {'order': order, 'item_form': item_form}
    return render(request, 'orders/order_detail.html', context)


def orderitem_delete(request, pk):
    order_item = get_object_or_404(OrderItem, pk=pk)
    order = order_item.order
    item_name = order_item.menu_item.name

    order_item.delete() # The signal in models.py handles the total calculation!

    messages.success(request, f'Removed "{item_name}" from the order.')
    return redirect('orders:order_detail', order_id=order.order_id)


# ==========================================
# ORDER CREATE & UPDATE
# ==========================================
def order_create(request):
    if request.method == 'POST':
        form = OrderForm(request.POST)
        if form.is_valid():
            order = form.save(commit=False) 

            customer_name = form.cleaned_data['customer_name'].strip()
            customer, created = Customer.objects.get_or_create(
                customer_name__iexact=customer_name,
                defaults={'customer_name': customer_name}
            )

            customer.phone_contact = form.cleaned_data['phone_contact']
            customer.email_address = form.cleaned_data['email_address']
            customer.save()

            order.customer = customer
            order.save()

            messages.success(request, f'Order started for {customer.customer_name}. Please add items below.')
            return redirect('orders:order_detail', order_id=order.order_id)
    else:
        form = OrderForm()

    return render(request, 'orders/order_form.html', {
        'form': form,
        'title': 'Create Order',
        'all_customers': Customer.objects.all().order_by('customer_name'),
    })


def order_update(request, order_id):
    order = get_object_or_404(Order, order_id=order_id)
    if request.method == 'POST':
        form = OrderForm(request.POST, instance=order)
        if form.is_valid():
            order = form.save(commit=False)
            
            customer_name = form.cleaned_data['customer_name'].strip()
            customer, created = Customer.objects.get_or_create(
                customer_name__iexact=customer_name,
                defaults={'customer_name': customer_name}
            )
            
            customer.phone_contact = form.cleaned_data['phone_contact']
            customer.email_address = form.cleaned_data['email_address']
            customer.save()
            
            order.customer = customer
            order.save()
            messages.success(request, 'Order updated successfully!')
            return redirect('orders:order_detail', order_id=order.order_id)
    else:
        form = OrderForm(instance=order)

    return render(request, 'orders/order_form.html', {
        'form': form,
        'title': 'Edit Order',
        'all_customers': Customer.objects.all().order_by('customer_name'),
    })


def order_delete(request, order_id):
    order = get_object_or_404(Order, order_id=order_id)
    if request.method == 'POST':
        order.delete()
        messages.success(request, 'Order deleted successfully!')
        return redirect('orders:order_list')
    return render(request, 'orders/confirm_delete.html', {'object': order, 'type': 'Order'})


# ==========================================
# CUSTOMER VIEWS
# ==========================================
def customer_list(request):
    customers = Customer.objects.all().order_by('customer_name')
    search_query = request.GET.get('search')
    if search_query:
        customers = customers.filter(Q(customer_name__icontains=search_query) | Q(email_address__icontains=search_query) | Q(phone_contact__icontains=search_query))
    return render(request, 'orders/customer_list.html', {'customers': customers, 'search_query': search_query})

def customer_create(request):
    if request.method == 'POST':
        form = CustomerForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Customer added successfully!')
            return redirect('orders:customer_list')
    else:
        form = CustomerForm()
    return render(request, 'orders/customer_form.html', {'form': form, 'title': 'Add Customer'})

def customer_update(request, pk):
    customer = get_object_or_404(Customer, customer_id=pk)
    if request.method == 'POST':
        form = CustomerForm(request.POST, instance=customer)
        if form.is_valid():
            form.save()
            messages.success(request, 'Customer updated successfully!')
            return redirect('orders:customer_list')
    else:
        form = CustomerForm(instance=customer)
    return render(request, 'orders/customer_form.html', {'form': form, 'title': 'Edit Customer'})

def customer_delete(request, pk):
    customer = get_object_or_404(Customer, customer_id=pk)
    if request.method == 'POST':
        customer.delete()
        messages.success(request, 'Customer deleted successfully!')
        return redirect('orders:customer_list')
    return render(request, 'orders/confirm_delete.html', {'object': customer, 'type': 'Customer'})


# ==========================================
# RESTAURANT, RIDER, MENU VIEWS
# ==========================================
def restaurant_list(request):
    restaurants = Restaurant.objects.all().order_by('name')
    search_query = request.GET.get('search')
    if search_query:
        restaurants = restaurants.filter(Q(name__icontains=search_query))
    return render(request, 'orders/restaurant_list.html', {'restaurants': restaurants, 'search_query': search_query})

def restaurant_create(request):
    if request.method == 'POST':
        form = RestaurantForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Restaurant added successfully!')
            return redirect('orders:restaurant_list')
    else:
        form = RestaurantForm()
    return render(request, 'orders/restaurant_form.html', {'form': form, 'title': 'Add Restaurant'})

def rider_list(request):
    riders = DeliveryRider.objects.all().order_by('name')
    status_filter = request.GET.get('status')
    if status_filter:
        riders = riders.filter(status=status_filter)
    rider_statuses = [('available', 'Available'), ('busy', 'Busy'), ('offline', 'Offline')]
    return render(request, 'orders/rider_list.html', {'riders': riders, 'statuses': rider_statuses, 'current_status': status_filter})

def rider_create(request):
    if request.method == 'POST':
        form = DeliveryRiderForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Rider added successfully!')
            return redirect('orders:rider_list')
    else:
        form = DeliveryRiderForm()
    return render(request, 'orders/rider_form.html', {'form': form, 'title': 'Add Rider'})

def menu_list(request):
    menu_items = MenuItem.objects.select_related('restaurant').filter(is_available=True).all().order_by('restaurant__name', 'name')
    restaurant_filter = request.GET.get('restaurant')
    if restaurant_filter:
        menu_items = menu_items.filter(restaurant_id=restaurant_filter)
    category_filter = request.GET.get('category')
    if category_filter:
        menu_items = menu_items.filter(category=category_filter)
    
    restaurants = Restaurant.objects.filter(is_open=True).all()
    categories = MenuItem.objects.values_list('category', flat=True).distinct()
    
    context = {
        'menu_items': menu_items, 'restaurants': restaurants, 'categories': categories,
        'selected_restaurant': restaurant_filter, 'selected_category': category_filter,
    }
    return render(request, 'orders/menu_list.html', context)

def menu_item_create(request):
    if request.method == 'POST':
        form = MenuItemForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Menu item added successfully!')
            return redirect('orders:menu_list')
    else:
        form = MenuItemForm()
    return render(request, 'orders/menu_item_form.html', {'form': form, 'title': 'Add Menu Item'})