from django.shortcuts import render, get_object_or_404
from django.db.models import Count, Sum, Avg, Q
from django.contrib import messages
from django.utils import timezone
from datetime import datetime, timedelta
from .models import Order, Customer, Restaurant, DeliveryRider, MenuItem, OrderItem

def dashboard(request):
    """Dashboard view showing key metrics"""
    
    # Get date range for today
    today = timezone.now().date()
    start_of_day = timezone.make_aware(datetime.combine(today, datetime.min.time()))
    
    # Statistics
    total_orders = Order.objects.count()
    pending_orders = Order.objects.filter(status='pending').count()
    delivered_orders = Order.objects.filter(status='delivered').count()
    today_orders = Order.objects.filter(placed_at__gte=start_of_day).count()
    
    total_customers = Customer.objects.filter(is_active=True).count()
    total_restaurants = Restaurant.objects.filter(is_open=True).count()
    available_riders = DeliveryRider.objects.filter(status='available').count()
    
    # Revenue
    total_revenue = Order.objects.filter(status='delivered').aggregate(Sum('total'))['total__sum'] or 0
    today_revenue = Order.objects.filter(
        status='delivered',
        placed_at__gte=start_of_day
    ).aggregate(Sum('total'))['total__sum'] or 0
    
    # Recent orders
    recent_orders = Order.objects.select_related(
        'customer', 'restaurant', 'rider'
    ).order_by('-placed_at')[:10]
    
    # Top customers
    top_customers = Customer.objects.annotate(
        order_count=Count('order'),
        total_spent=Sum('order__total')
    ).filter(order_count__gt=0).order_by('-total_spent')[:5]
    
    # Top restaurants
    top_restaurants = Restaurant.objects.annotate(
        order_count=Count('order'),
        total_revenue=Sum('order__total')
    ).filter(order_count__gt=0).order_by('-order_count')[:5]
    
    # Popular menu items
    popular_items = MenuItem.objects.annotate(
        order_count=Count('orderitem')
    ).filter(order_count__gt=0).order_by('-order_count')[:10]
    
    # Recent delivery activity
    recent_deliveries = Order.objects.filter(
        rider__isnull=False,
        status='delivered'
    ).select_related('rider', 'customer').order_by('-actual_delivery_time')[:5]
    
    context = {
        'total_orders': total_orders,
        'pending_orders': pending_orders,
        'delivered_orders': delivered_orders,
        'today_orders': today_orders,
        'total_customers': total_customers,
        'total_restaurants': total_restaurants,
        'available_riders': available_riders,
        'total_revenue': total_revenue,
        'today_revenue': today_revenue,
        'recent_orders': recent_orders,
        'top_customers': top_customers,
        'top_restaurants': top_restaurants,
        'popular_items': popular_items,
        'recent_deliveries': recent_deliveries,
    }
    
    return render(request, 'orders/dashboard.html', context)

def order_list(request):
    """Display all orders with filters"""
    
    orders = Order.objects.select_related(
        'customer', 'restaurant', 'rider'
    ).all().order_by('-placed_at')
    
    # Filter by status
    status_filter = request.GET.get('status')
    if status_filter:
        orders = orders.filter(status=status_filter)
    
    # Search
    search_query = request.GET.get('search')
    if search_query:
        orders = orders.filter(
            Q(customer__name__icontains=search_query) |
            Q(restaurant__name__icontains=search_query) |
            Q(delivery_address__icontains=search_query)
        )
    
    # Order statuses for filter dropdown
    statuses = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('preparing', 'Preparing'),
        ('ready', 'Ready'),
        ('delivering', 'Delivering'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    ]
    
    context = {
        'orders': orders,
        'statuses': statuses,
        'current_status': status_filter,
        'search_query': search_query,
    }
    
    return render(request, 'orders/order_list.html', context)

def order_detail(request, order_id):
    """Display order details"""
    
    order = get_object_or_404(
        Order.objects.select_related(
            'customer', 'restaurant', 'rider'
        ).prefetch_related(
            'orderitem_set__menu_item'
        ),
        order_id=order_id
    )
    
    # Calculate subtotal (without delivery fee)
    subtotal = sum(item.quantity * item.unit_price for item in order.orderitem_set.all())
    
    context = {
        'order': order,
        'subtotal': subtotal,
    }
    
    return render(request, 'orders/order_detail.html', context)

def customer_list(request):
    """Display all customers"""
    
    customers = Customer.objects.filter(is_active=True).all().order_by('name')
    
    search_query = request.GET.get('search')
    if search_query:
        customers = customers.filter(
            Q(name__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(city__icontains=search_query)
        )
    
    context = {
        'customers': customers,
        'search_query': search_query,
    }
    
    return render(request, 'orders/customer_list.html', context)

def restaurant_list(request):
    """Display all restaurants"""
    
    restaurants = Restaurant.objects.all().order_by('name')
    
    search_query = request.GET.get('search')
    if search_query:
        restaurants = restaurants.filter(
            Q(name__icontains=search_query) |
            Q(cuisine_type__icontains=search_query)
        )
    
    context = {
        'restaurants': restaurants,
        'search_query': search_query,
    }
    
    return render(request, 'orders/restaurant_list.html', context)

def rider_list(request):
    """Display all delivery riders"""
    
    riders = DeliveryRider.objects.filter(is_active=True).all().order_by('name')
    
    status_filter = request.GET.get('status')
    if status_filter:
        riders = riders.filter(status=status_filter)
    
    rider_statuses = [
        ('available', 'Available'),
        ('busy', 'Busy'),
        ('offline', 'Offline'),
    ]
    
    context = {
        'riders': riders,
        'statuses': rider_statuses,
        'current_status': status_filter,
    }
    
    return render(request, 'orders/rider_list.html', context)

def menu_list(request):
    """Display all menu items"""
    
    menu_items = MenuItem.objects.select_related('restaurant').filter(
        is_available=True
    ).all().order_by('restaurant__name', 'name')
    
    restaurant_filter = request.GET.get('restaurant')
    if restaurant_filter:
        menu_items = menu_items.filter(restaurant_id=restaurant_filter)
    
    category_filter = request.GET.get('category')
    if category_filter:
        menu_items = menu_items.filter(category=category_filter)
    
    # Get all restaurants for filter
    restaurants = Restaurant.objects.filter(is_open=True).all()
    
    # Get all categories
    categories = MenuItem.objects.values_list('category', flat=True).distinct()
    
    context = {
        'menu_items': menu_items,
        'restaurants': restaurants,
        'categories': categories,
        'selected_restaurant': restaurant_filter,
        'selected_category': category_filter,
    }
    
    return render(request, 'orders/menu_list.html', context)