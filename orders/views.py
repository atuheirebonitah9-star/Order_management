from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Count, Sum, Avg, Q
from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.utils import timezone
from django.db.models.functions import TruncDay, TruncHour, TruncMonth
from django.templatetags.static import static
from datetime import datetime, timedelta
from .models import Order, Customer, Restaurant, DeliveryRider, MenuItem, OrderItem
from .forms import (
    CustomerForm, RestaurantForm, DeliveryRiderForm, 
    MenuItemForm, OrderForm, OrderItemForm
)

def dashboard(request):
    today = timezone.now().date()
    start_of_day = timezone.make_aware(datetime.combine(today, datetime.min.time()))

    month_starts = []
    for offset in range(11, -1, -1):
        month_index = today.year * 12 + today.month - 1 - offset
        year, month_index = divmod(month_index, 12)
        month_starts.append(datetime(year, month_index + 1, 1).date())

    chart_start = timezone.make_aware(datetime.combine(month_starts[0], datetime.min.time()))
    if today.month == 12:
        next_month = datetime(today.year + 1, 1, 1)
    else:
        next_month = datetime(today.year, today.month + 1, 1)
    chart_end = timezone.make_aware(next_month)

    monthly_order_totals = {
        month.strftime('%Y-%m'): total
        for month, total in Order.objects.filter(
            placed_at__gte=chart_start,
            placed_at__lt=chart_end,
        ).annotate(month=TruncMonth('placed_at')).values(
            'month'
        ).annotate(total=Count('order_id')).values_list('month', 'total')
    }
    monthly_order_labels = [month.strftime('%b') for month in month_starts]
    monthly_order_counts = [
        monthly_order_totals.get(month.strftime('%Y-%m'), 0)
        for month in month_starts
    ]
    
    total_orders = Order.objects.count()
    pending_orders = Order.objects.filter(status='pending').count()
    delivered_orders = Order.objects.filter(delivery_status='delivered').count()
    today_orders = Order.objects.filter(placed_at__gte=start_of_day).count()
    
    total_customers = Customer.objects.count()
    total_restaurants = Restaurant.objects.filter(is_open=True).count()
    available_riders = DeliveryRider.objects.filter(status='available').count()
    available_rider_preview = DeliveryRider.objects.filter(
        status='available'
    ).order_by('name')[:3]
    
    total_revenue = Order.objects.filter(status='completed').aggregate(Sum('total'))['total__sum'] or 0
    today_revenue = Order.objects.filter(
        status='completed',
        placed_at__gte=start_of_day
    ).aggregate(Sum('total'))['total__sum'] or 0
    
    recent_orders = Order.objects.select_related('customer', 'restaurant', 'rider').order_by('-placed_at')[:10]
    top_customers = Customer.objects.annotate(order_count=Count('order'), total_spent=Sum('order__total')).filter(order_count__gt=0).order_by('-total_spent')[:5]
    top_restaurants = Restaurant.objects.annotate(order_count=Count('order'), total_revenue=Sum('order__total')).filter(order_count__gt=0).order_by('-order_count')[:5]
    popular_items = MenuItem.objects.annotate(order_count=Count('orderitem')).filter(order_count__gt=0).order_by('-order_count')[:10]
    status_totals = dict(
        Order.objects.values('status').annotate(total=Count('order_id')).values_list('status', 'total')
    )
    status_labels = [label for _, label in Order.ORDER_STATUS]
    status_counts = [status_totals.get(value, 0) for value, _ in Order.ORDER_STATUS]
    
    context = {
        'total_orders': total_orders, 'pending_orders': pending_orders, 'delivered_orders': delivered_orders,
        'today_orders': today_orders, 'total_customers': total_customers, 'total_restaurants': total_restaurants,
        'available_riders': available_riders, 'total_revenue': total_revenue, 'today_revenue': today_revenue,
        'available_rider_preview': available_rider_preview,
        'recent_orders': recent_orders, 'top_customers': top_customers, 'top_restaurants': top_restaurants,
        'popular_items': popular_items,
        'monthly_order_labels': monthly_order_labels, 'monthly_order_counts': monthly_order_counts,
        'status_labels': status_labels, 'status_counts': status_counts,
    }
    return render(request, 'orders/dashboard.html', context)


def order_list(request):
    orders = Order.objects.select_related('customer', 'restaurant', 'rider').all().order_by('-placed_at')
    order_total = orders.count()
    status_totals = dict(
        Order.objects.values('status').annotate(total=Count('order_id')).values_list('status', 'total')
    )
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
    status_overview = [
        {'value': value, 'label': label, 'count': status_totals.get(value, 0)}
        for value, label in statuses
    ]
    context = {
        'orders': orders,
        'statuses': statuses,
        'current_status': status_filter,
        'search_query': search_query,
        'order_total': order_total,
        'status_overview': status_overview,
    }
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
    customers = Customer.objects.annotate(
        order_count=Count('order', distinct=True),
        total_spent=Sum('order__total'),
    ).order_by('customer_name')
    customer_total = Customer.objects.count()
    customers_with_orders = Customer.objects.filter(order__isnull=False).distinct().count()
    search_query = request.GET.get('search')
    if search_query:
        customers = customers.filter(Q(customer_name__icontains=search_query) | Q(email_address__icontains=search_query) | Q(phone_contact__icontains=search_query))
    return render(request, 'orders/customer_list.html', {
        'customers': customers,
        'search_query': search_query,
        'customer_total': customer_total,
        'customers_with_orders': customers_with_orders,
    })

def customer_create(request):
    if request.method == 'POST':
        form = CustomerForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Customer added successfully!')
            return redirect('orders:customer_list')
    else:
        form = CustomerForm()
    return render(request, 'orders/entity_form.html', {'form': form, 'title': 'Add Customer'})

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
    return render(request, 'orders/entity_form.html', {'form': form, 'title': 'Edit Customer'})

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
    restaurants = Restaurant.objects.annotate(
        order_count=Count('order', distinct=True),
        total_revenue=Sum('order__total', filter=Q(order__status='completed')),
    ).order_by('name')
    restaurant_total = Restaurant.objects.count()
    open_restaurants = Restaurant.objects.filter(is_open=True).count()
    closed_restaurants = restaurant_total - open_restaurants
    restaurant_order_total = Order.objects.count()
    restaurant_revenue = Order.objects.filter(status='completed').aggregate(
        total=Sum('total')
    )['total'] or 0
    search_query = request.GET.get('search')
    if search_query:
        restaurants = restaurants.filter(
            Q(name__icontains=search_query) | Q(address__icontains=search_query)
        )
    return render(request, 'orders/restaurant_list.html', {
        'restaurants': restaurants,
        'search_query': search_query,
        'restaurant_total': restaurant_total,
        'open_restaurants': open_restaurants,
        'closed_restaurants': closed_restaurants,
        'restaurant_order_total': restaurant_order_total,
        'restaurant_revenue': restaurant_revenue,
    })

def restaurant_create(request):
    if request.method == 'POST':
        form = RestaurantForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Restaurant added successfully!')
            return redirect('orders:restaurant_list')
    else:
        form = RestaurantForm()
    return render(request, 'orders/entity_form.html', {'form': form, 'title': 'Add Restaurant'})

def rider_list(request):
    riders = DeliveryRider.objects.annotate(
        order_count=Count('order', distinct=True),
        delivered_count=Count('order', filter=Q(order__delivery_status='delivered'), distinct=True),
    ).order_by('name')
    status_filter = request.GET.get('status')
    if status_filter:
        riders = riders.filter(status=status_filter)
    search_query = request.GET.get('search')
    if search_query:
        riders = riders.filter(Q(name__icontains=search_query) | Q(rider_id__icontains=search_query))
    rider_statuses = [('available', 'Available'), ('busy', 'Busy'), ('offline', 'Offline')]
    rider_counts = dict(
        DeliveryRider.objects.values('status').annotate(total=Count('rider_id')).values_list('status', 'total')
    )
    return render(request, 'orders/rider_list.html', {
        'riders': riders,
        'statuses': rider_statuses,
        'current_status': status_filter,
        'search_query': search_query,
        'rider_total': DeliveryRider.objects.count(),
        'rider_status_overview': [
            {'value': value, 'label': label, 'count': rider_counts.get(value, 0)}
            for value, label in rider_statuses
        ],
    })

def rider_create(request):
    if request.method == 'POST':
        form = DeliveryRiderForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Rider added successfully!')
            return redirect('orders:rider_list')
    else:
        form = DeliveryRiderForm()
    return render(request, 'orders/entity_form.html', {'form': form, 'title': 'Add Rider'})

def menu_list(request):
    menu_items = MenuItem.objects.select_related('restaurant').annotate(
        times_ordered=Count('orderitem', distinct=True),
        quantity_ordered=Sum('orderitem__quantity'),
    ).order_by('restaurant__name', 'name')
    restaurant_filter = request.GET.get('restaurant')
    if restaurant_filter:
        menu_items = menu_items.filter(restaurant_id=restaurant_filter)
    category_filter = request.GET.get('category')
    if category_filter:
        menu_items = menu_items.filter(category=category_filter)
    availability_filter = request.GET.get('availability')
    if availability_filter == 'available':
        menu_items = menu_items.filter(is_available=True)
    elif availability_filter == 'unavailable':
        menu_items = menu_items.filter(is_available=False)
    search_query = request.GET.get('search')
    if search_query:
        menu_items = menu_items.filter(
            Q(name__icontains=search_query) |
            Q(category__icontains=search_query) |
            Q(restaurant__name__icontains=search_query)
        )
    
    restaurants = Restaurant.objects.all().order_by('name')
    categories = MenuItem.objects.order_by('category').values_list('category', flat=True).distinct()
    menu_item_total = MenuItem.objects.count()
    available_item_total = MenuItem.objects.filter(is_available=True).count()
    unavailable_item_total = menu_item_total - available_item_total
    menu_image_paths = {
        'Beef Burger': 'orders/images/beef_burger.jpg',
        'Chapati Rolls': 'orders/images/chapati_rolls.jfif',
        'Chicken BBQ Pizza': 'orders/images/chicken_pizza.jpg',
        'Chips': 'orders/images/chips.jfif',
        'Chocolate Brownie': 'orders/images/chocolate_brownie.jfif',
        'Fresh Passion Juice': 'orders/images/freshpassionjuice.jpg',
        'Fruit Salad': 'orders/images/fruit_salads.jfif',
        'Garlic Bread': 'orders/images/garlic_bread.jfif',
        'Ginger Tea': 'orders/images/ginger_tea.jfif',
        'Grilled Chicken Half': 'orders/images/grilledchickenHalf.jpg',
        'Luwombo Chicken': 'orders/images/luwombo_chicken.jfif',
        'Margherita Pizza': 'orders/images/margherita-pizza.jpg',
        'Matooke & Groundnut Sauce': 'orders/images/matooke&groundnuts.jfif',
        'Millet Porridge': 'orders/images/millet_porridge.jfif',
        'Rolex Special': 'orders/images/rolex_special.jfif',
        'Samosas (4)': 'orders/images/samosas.jpg',
        'Soda 500ml': 'orders/images/sodda_500ml.jfif',
        'Tilapia Fillet': 'orders/images/tilapia_fillet.jfif',
    }
    for item in menu_items:
        image_path = menu_image_paths.get(item.name)
        item.image_url = static(image_path) if image_path else None
    
    context = {
        'menu_items': menu_items, 'restaurants': restaurants, 'categories': categories,
        'selected_restaurant': restaurant_filter, 'selected_category': category_filter,
        'availability_filter': availability_filter, 'search_query': search_query,
        'menu_item_total': menu_item_total, 'available_item_total': available_item_total,
        'unavailable_item_total': unavailable_item_total,
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
    return render(request, 'orders/entity_form.html', {'form': form, 'title': 'Add Menu Item'})


# ==========================================
# REPORTS (staff only)
# ==========================================
@user_passes_test(lambda u: u.is_staff)
def reports(request):
    revenue_by_restaurant = Restaurant.objects.annotate(
        revenue=Sum('order__total', filter=Q(order__status='completed')),
        orders=Count('order', distinct=True)
    ).order_by('-revenue')

    periods = {
        '1D': 'Last 24 hours',
        '1W': 'Last 7 days',
        '1M': 'Last 30 days',
        '6M': 'Last 6 months',
        '1Y': 'Last 12 months',
        'ALL': 'All time',
    }
    selected_period = request.GET.get('period', '1M').upper()
    if selected_period not in periods:
        selected_period = '1M'

    now = timezone.now()
    local_today = timezone.localdate(now)
    if selected_period == '1D':
        current_hour = now.replace(minute=0, second=0, microsecond=0)
        bucket_starts = [
            current_hour - timedelta(hours=offset)
            for offset in range(23, -1, -1)
        ]
        period_start = bucket_starts[0]
        period_end = current_hour + timedelta(hours=1)
        bucket_function = TruncHour('placed_at')
        bucket_key = lambda value: timezone.localtime(value).strftime('%Y-%m-%d %H')
        chart_labels = [timezone.localtime(value).strftime('%H:%M') for value in bucket_starts]
        previous_start = period_start - timedelta(days=1)
        previous_end = period_start
    elif selected_period in ('1W', '1M'):
        day_count = 7 if selected_period == '1W' else 30
        first_day = local_today - timedelta(days=day_count - 1)
        period_start = timezone.make_aware(datetime.combine(first_day, datetime.min.time()))
        next_day = local_today + timedelta(days=1)
        period_end = timezone.make_aware(datetime.combine(next_day, datetime.min.time()))
        bucket_starts = [first_day + timedelta(days=offset) for offset in range(day_count)]
        bucket_function = TruncDay('placed_at')
        bucket_key = lambda value: timezone.localtime(value).date()
        chart_labels = [value.strftime('%d %a') for value in bucket_starts]
        previous_start = period_start - timedelta(days=day_count)
        previous_end = period_start
    else:
        current_month = datetime(local_today.year, local_today.month, 1)
        if selected_period == 'ALL':
            first_completed_order = Order.objects.filter(status='completed').order_by(
                'placed_at'
            ).values_list('placed_at', flat=True).first()
            first_month = (
                datetime(first_completed_order.year, first_completed_order.month, 1)
                if first_completed_order else current_month
            )
            month_count = (
                (current_month.year - first_month.year) * 12
                + current_month.month - first_month.month + 1
            )
        else:
            month_count = 6 if selected_period == '6M' else 12
            month_index = current_month.year * 12 + current_month.month - 1 - (month_count - 1)
            first_year, first_month_index = divmod(month_index, 12)
            first_month = datetime(first_year, first_month_index + 1, 1)

        bucket_starts = []
        for offset in range(month_count):
            month_index = first_month.year * 12 + first_month.month - 1 + offset
            year, month_index = divmod(month_index, 12)
            bucket_starts.append(datetime(year, month_index + 1, 1))

        period_start = timezone.make_aware(bucket_starts[0])
        next_month_index = current_month.year * 12 + current_month.month
        next_year, next_month_index = divmod(next_month_index, 12)
        period_end = timezone.make_aware(datetime(next_year, next_month_index + 1, 1))
        bucket_function = TruncMonth('placed_at')
        bucket_key = lambda value: timezone.localtime(value).strftime('%Y-%m')
        chart_labels = [value.strftime('%b %y') for value in bucket_starts]
        if selected_period == 'ALL':
            previous_start = previous_end = None
        else:
            previous_start = period_start - (period_end - period_start)
            previous_end = period_start

    bucket_totals = {
        bucket_key(bucket): float(total or 0)
        for bucket, total in Order.objects.filter(
            status='completed',
            placed_at__gte=period_start,
            placed_at__lt=period_end,
        ).annotate(bucket=bucket_function).values(
            'bucket'
        ).annotate(total=Sum('total')).values_list('bucket', 'total')
    }
    if selected_period == '1D':
        chart_values = [
            bucket_totals.get(timezone.localtime(value).strftime('%Y-%m-%d %H'), 0)
            for value in bucket_starts
        ]
    elif selected_period in ('1W', '1M'):
        chart_values = [bucket_totals.get(value, 0) for value in bucket_starts]
    else:
        chart_values = [
            bucket_totals.get(value.strftime('%Y-%m'), 0)
            for value in bucket_starts
        ]

    period_revenue = Order.objects.filter(
        status='completed',
        placed_at__gte=period_start,
        placed_at__lt=period_end,
    ).aggregate(total=Sum('total'))['total'] or 0
    previous_revenue = None
    period_change = None
    if previous_start is not None:
        previous_revenue = Order.objects.filter(
            status='completed',
            placed_at__gte=previous_start,
            placed_at__lt=previous_end,
        ).aggregate(total=Sum('total'))['total'] or 0
        if previous_revenue:
            period_change = round(
                (float(period_revenue) - float(previous_revenue)) / float(previous_revenue) * 100,
                1,
            )

    status_totals = dict(
        Order.objects.values('status').annotate(n=Count('order_id')).values_list('status', 'n')
    )
    by_status = [
        {'status': label, 'n': status_totals.get(value, 0)}
        for value, label in Order.ORDER_STATUS
        if status_totals.get(value, 0)
    ]
    report_totals = Order.objects.aggregate(
        total_orders=Count('order_id'),
        completed_orders=Count('order_id', filter=Q(status='completed')),
        completed_revenue=Sum('total', filter=Q(status='completed')),
        average_order=Avg('total', filter=Q(status='completed')),
        delivered_orders=Count('order_id', filter=Q(delivery_status='delivered')),
    )

    best_items = MenuItem.objects.annotate(
        qty=Sum('orderitem__quantity')
    ).filter(qty__gt=0).select_related('restaurant').order_by('-qty')[:10]

    riders = DeliveryRider.objects.annotate(
        total=Count('order'),
        delivered=Count('order', filter=Q(order__delivery_status='delivered')),
    ).order_by('-delivered')

    context = {
        **report_totals,
        'revenue_chart': {
            'labels': chart_labels,
            'values': chart_values,
        },
        'revenue_by_restaurant': revenue_by_restaurant,
        'selected_period': selected_period,
        'period_choices': periods,
        'period_label': periods[selected_period],
        'period_revenue': period_revenue,
        'period_change': period_change,
        'status_chart': {
            'labels': [s['status'].title() for s in by_status],
            'values': [s['n'] for s in by_status],
        },
        'best_items': best_items,
        'riders': riders,
    }
    return render(request, 'orders/reports.html', context)