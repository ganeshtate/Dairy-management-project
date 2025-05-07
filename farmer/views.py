from django.shortcuts import render,redirect,get_object_or_404
from myapp.models import Addfarmer,MilkCollection
from django.contrib import messages
from myapp.models import Cattlefeed,FeedOrder
from django.contrib.auth.models import User
from django.db.models import Sum,Avg
from decimal import Decimal, ROUND_DOWN
from django.http import HttpResponse
from datetime import datetime,date,timedelta,timezone
import calendar
from collections import defaultdict
from statistics import mean
from django.contrib.auth.decorators import login_required
import datetime
from django.utils import timezone 
from calendar import monthrange


# Create your views here.

def login(request):
    if request.method == 'POST':
        df_code = request.POST.get('df_code')
        farmer_name = request.POST.get('farmer_name')

        try:
            farmer = Addfarmer.objects.get(df_code=df_code, farmer_name=farmer_name)
            request.session['farmer_id'] = farmer.id  # Save farmer's ID in session
            return redirect('dashboard')
        except Addfarmer.DoesNotExist:
            messages.error(request, "Invalid DF Code or Farmer Name")

    return render(request, 'farmer/farmer_login.html')  # Correct path

from collections import defaultdict

def dashboard(request):
    farmer_id = request.session.get('farmer_id')
    farmer_name = request.session.get('farmer_name')

    if not farmer_id:
        return render(request, 'farmer/farmer_login.html', {'error': 'Please login first'})

    farmer = get_object_or_404(Addfarmer, id=farmer_id)

    today = timezone.now().date()
    day = today.day

    # Determine muster period
    if day <= 10:
        start_date = today.replace(day=1)
        end_date = today.replace(day=10)
    elif day <= 20:
        start_date = today.replace(day=11)
        end_date = today.replace(day=20)
    else:
        start_date = today.replace(day=21)
        next_month = today.replace(day=28) + datetime.timedelta(days=4)
        end_date = next_month - datetime.timedelta(days=next_month.day)

    # Fetch milk and feed data
    milk_entries = MilkCollection.objects.filter(
        farmer_id=farmer_id,
        date__range=(start_date, end_date)
    ).order_by('date', 'shift')

    feed_orders = FeedOrder.objects.filter(
        farmer_id=farmer_id,
        ordered_at__range=(start_date, end_date)
    ).order_by('ordered_at')

    ordered_feed_amount = feed_orders.aggregate(Sum('total_price'))['total_price__sum'] or 0

    # Group milk entries by date
    daily_milk = defaultdict(list)
    for entry in milk_entries:
        daily_milk[entry.date].append(entry)

    cow_data = {'total_litre': 0, 'total_fat': 0, 'total_rate': 0, 'total_amount': 0}
    buffalo_data = {'total_litre': 0, 'total_fat': 0, 'total_rate': 0, 'total_amount': 0}

    for entry in milk_entries:
        if entry.animal_type == 'cow':
            cow_data['total_litre'] += entry.litre
            cow_data['total_fat'] += entry.fat
            cow_data['total_rate'] += entry.rate
            cow_data['total_amount'] += entry.amount
        elif entry.animal_type == 'buffalo':
            buffalo_data['total_litre'] += entry.litre
            buffalo_data['total_fat'] += entry.fat
            buffalo_data['total_rate'] += entry.rate
            buffalo_data['total_amount'] += entry.amount

    if cow_data['total_litre'] > 0:
        cow_data['avg_fat'] = cow_data['total_fat'] / cow_data['total_litre']
        cow_data['avg_rate'] = cow_data['total_rate'] / cow_data['total_litre']
    else:
        cow_data['avg_fat'] = 0
        cow_data['avg_rate'] = 0

    if buffalo_data['total_litre'] > 0:
        buffalo_data['avg_fat'] = buffalo_data['total_fat'] / buffalo_data['total_litre']
        buffalo_data['avg_rate'] = buffalo_data['total_rate'] / buffalo_data['total_litre']
    else:
        buffalo_data['avg_fat'] = 0
        buffalo_data['avg_rate'] = 0

    total_litre = cow_data['total_litre'] + buffalo_data['total_litre']
    avg_fat = (cow_data['total_fat'] + buffalo_data['total_fat']) / total_litre if total_litre > 0 else 0
    avg_rate = (cow_data['total_rate'] + buffalo_data['total_rate']) / total_litre if total_litre > 0 else 0
    total_amount = cow_data['total_amount'] + buffalo_data['total_amount']
    final_amount = float(total_amount) - float(ordered_feed_amount)

    dashboard_data = {
        'cow': cow_data,
        'buffalo': buffalo_data,
        'total_litre': total_litre,
        'avg_fat': avg_fat,
        'avg_rate': avg_rate,
        'total_amount': total_amount,
        'ordered_feed_amount': ordered_feed_amount,
        'final_amount': final_amount
    }

    context = {
        'farmer': farmer,
        'dashboard_data': dashboard_data,
        'milk_entries': milk_entries,
        'feed_orders': feed_orders,
        'start_date': start_date,
        'end_date': end_date,
        'daily_milk': dict(daily_milk)  # Pass the grouped milk data
    }

    return render(request, 'farmer/dashboard.html', context)


def logout(request):
    request.session.flush()  # remove all session data
    return redirect('login')

def products(request):
    farmer_id = request.session.get('farmer_id')
    if not farmer_id:
        messages.error(request, "Please log in first.")
        return redirect('login')

    farmer = Addfarmer.objects.get(id=farmer_id)
    products = Cattlefeed.objects.all()

    # 🛠 Fetch milk collection total and order total
    milk_collection_total = MilkCollection.objects.filter(farmer=farmer).aggregate(total=Sum('amount'))['total'] or 0
    feed_order_total = FeedOrder.objects.filter(farmer=farmer).aggregate(total=Sum('total_price'))['total'] or 0

    # 💥 Fix: convert both to Decimal before subtracting
    milk_collection_total = Decimal(milk_collection_total)
    feed_order_total = Decimal(feed_order_total)

    milk_balance = milk_collection_total - feed_order_total

    # Round the value to 2 decimal places
    milk_balance = milk_balance.quantize(Decimal('0.00'), rounding=ROUND_DOWN)

    # Pass the milk_balance to the products page context
    return render(request, 'farmer/products.html', {
        'products': products,
        'farmer': farmer,
        'milk_balance': milk_balance,
    })




def place_order(request, product_id):
    farmer_id = request.session.get('farmer_id')
    if not farmer_id:
        messages.error(request, "Please log in first.")
        return redirect('login')

    try:
        farmer = Addfarmer.objects.get(id=farmer_id)
    except Addfarmer.DoesNotExist:
        messages.error(request, "Farmer not found.")
        return redirect('login')

    if request.method == 'POST':
        try:
            quantity = int(request.POST['quantity'])
        except (KeyError, ValueError):
            messages.error(request, "Invalid quantity input.")
            return redirect('products')

        product = get_object_or_404(Cattlefeed, id=product_id)

        # Fetch milk collection and feed order totals
        milk_collection_total = MilkCollection.objects.filter(farmer=farmer).aggregate(total=Sum('amount'))['total'] or 0
        feed_order_total = FeedOrder.objects.filter(farmer=farmer).aggregate(total=Sum('total_price'))['total'] or 0

        # Convert to Decimal
        milk_collection_total = Decimal(milk_collection_total)
        feed_order_total = Decimal(feed_order_total)

        milk_balance = milk_collection_total - feed_order_total

        total_price = product.price * quantity

        # Check balance
        if milk_balance < total_price:
            messages.error(request, "Not enough balance to place this order.")
            return redirect('products')

        # Place the order
        FeedOrder.objects.create(
            farmer=farmer,
            product=product,
            quantity=quantity,
            total_price=total_price
        )

        # Update stock
        product.available_stock -= quantity
        product.save()

        messages.success(request, "Order placed successfully!")
        return redirect('products')

    return redirect('products')
