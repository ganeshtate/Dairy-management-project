from django.shortcuts import render, get_object_or_404, redirect
from .models import Addfarmer
from django.db import IntegrityError
from django.contrib import messages
from datetime import datetime
from .models import  MilkCollection
from django.db.models import Avg, Sum
from datetime import date, timedelta
from .models import Cattlefeed,FeedOrder
from datetime import timedelta
from django.utils import timezone
import calendar





# Create your views here.
def gethomepage(request):
    return render(request,('index.html'))
def farmer(request):
    return render(request,('farmer.html'))
def show_farmers(request):
    data = Addfarmer.objects.all()  
    return render(request, "show_farmers.html", {'data': data})
def collect_milk(request):
        return render(request,'collect_milk.html')



def add_farmer(request):
    if request.method == 'POST':
        df_code = request.POST.get('df_code')
        farmer_name = request.POST.get('farmer_name')
        contact = request.POST.get('contact')
        address = request.POST.get('address')
        date = request.POST.get('date')

        try:
            # Optional: Convert string date to Python date object
            if date:
                date = datetime.strptime(date, '%Y-%m-%d').date()

            Addfarmer.objects.create(
                df_code=df_code,
                farmer_name=farmer_name,
                contact=contact,
                address=address,
                date=date
            )
            messages.success(request, 'Farmer added successfully')
            return redirect('farmer')  # Update this to your actual redirect URL name

        except IntegrityError:
            message = "Farmer with this name or code already exists. Please use another name or code."
            return render(request, 'farmer.html', {'message': message})

    return render(request, 'farmer.html')


def delete(request):
    id = request.GET['df_code']
    Addfarmer.objects.filter(df_code=id).delete()
    return redirect('show_farmers') 
def edit_farmer(request):
    df_code=request.GET['df_code']
    farmer_name='not_found'
    for data in Addfarmer.objects.filter(df_code=df_code):
        farmer_name=data.farmer_name
        contact=data.contact
        address=data.address
        date=data.date
    return render(request,'edit_farmer.html',{'df_code':df_code,'farmer_name':farmer_name})


def update_farmer(request):
    if request.method == 'POST':
        df_code = request.POST.get('df_code')
        farmer_name = request.POST.get('farmer_name')
        contact = request.POST.get('contact')
        address = request.POST.get('address')
        date = request.POST.get('date')

        # Find the farmer by df_code
        farmer = Addfarmer.objects.filter(df_code=df_code).first()  # Using first() to safely get the object

        if farmer:  # Check if the farmer exists
            # Update the farmer's details
            farmer.df_code=df_code
            farmer.farmer_name = farmer_name
            farmer.contact = contact
            farmer.address = address
            farmer.date = date
            farmer.save()  # Save the updated object

            messages.success(request, 'Farmer updated successfully!')
            return redirect('show_farmers')
        else:
            messages.error(request, 'Farmer not found with the provided DF Code!')
            return render(request, 'edit_farmer.html', {'message': 'Farmer not found', 'df_code': df_code})

    return redirect('show_farmers')  # Redirect if it's a GET request




def calculate_rate(animal_type, fat, snf):
    fat = float(fat)
    snf = float(snf)

    if animal_type == "cow":
        fat_rate = 7.0  # per 1% fat
        snf_rate = 3.0  # per 1% SNF
    else:  # buffalo
        fat_rate = 9.0
        snf_rate = 4.0

    return round((fat * fat_rate) + (snf * snf_rate), 2)

def calculate_rate(fat, snf, animal_type):
    if animal_type == 'cow':
        base_rate = 35  # Base rate for cow milk at 3.5% fat, 8.5% SNF
        fat_rate = 5    # Rate per 0.5% increase in fat for cow
        snf_rate = 2    # Rate adjustment for SNF in cow milk
    else:
        base_rate = 50  # Base rate for buffalo milk at 6.0% fat, 8.5% SNF (adjusted)
        fat_rate = 10   # Rate per 0.5% increase in fat for buffalo
        snf_rate = 3    # Rate adjustment for SNF in buffalo milk

    # Adjust for fat content
    fat_difference = fat - (10.0 if animal_type == 'buffalo' else 3.5)
    rate = base_rate + (fat_difference * fat_rate)

    # Ensure buffalo milk's rate is always higher than cow milk
    if animal_type == 'buffalo' and rate < 50:
        rate = 50  # Make sure buffalo milk doesn't fall below ₹50

    # Adjust for SNF content
    snf_difference = snf - 8.5
    rate += snf_difference * snf_rate

    return round(rate, 2)

def collect_milk(request):
    if request.method == "POST":
        df_code = request.POST.get("df_code")
        shift = request.POST.get("shift")
        animal_type = request.POST.get("animal_type")
        litre = float(request.POST.get("litre"))
        fat = float(request.POST.get("fat"))
        snf = float(request.POST.get("snf"))
        degree = float(request.POST.get("degree"))
        rate = float(request.POST.get("rate"))
        amount = float(request.POST.get("amount"))
        date = request.POST.get("date")

        try:
            # Try to get the farmer based on the df_code
            farmer = Addfarmer.objects.get(df_code=df_code)
        except Addfarmer.DoesNotExist:
            # If the farmer is not found, show an error message and redirect
            messages.error(request, "❌ Farmer not found. Please check the DF Code.")
            return redirect("collect_milk")

        # Check for duplicate entry (same shift, animal, and date)
        if MilkCollection.objects.filter(
            farmer=farmer,
            shift=shift,
            animal_type=animal_type,
            date=date
        ).exists():
            messages.error(
                request,
                f"❌ Milk for farmer **{farmer.farmer_name}** ({df_code}), shift **{shift.title()}**, and animal type **{animal_type.title()}** is already collected for today!"
            )
            return redirect("collect_milk")

        # Save the milk collection entry
        milk_collection = MilkCollection(
            farmer=farmer,
            animal_type=animal_type,
            shift=shift,
            litre=litre,
            fat=fat,
            snf=snf,
            degree=degree,
            rate=rate,
            amount=amount,
            date=date
        )
        milk_collection.save()

        # Send SMS to the farmer
        message_text = (
            f"Dear {farmer.farmer_name},\n"
            f"Milk collected successfully:\n"
            f"Shift: {shift.title()} | Animal: {animal_type.title()}\n"
            f"Litres: {litre} | Fat: {fat} | SNF: {snf} | Degree: {degree}\n"
            f"Rate: ₹{rate}/L | Total: ₹{amount}\n"
            "Thank you for your contribution!"
        )

        # Provide the number directly here (Example: Twilio trial or your number)
        # Replace with the actual recipient number
        

        messages.success(request, "✅ Milk collection saved successfully!")
        return redirect("collect_milk")

    return render(request, "collect_milk.html")






def generate_report(request):
    if request.method == "POST":
        df_code = request.POST.get('df_code')
        
        # Get the farmer's data based on DF code
        try:
            farmer = Addfarmer.objects.get(df_code=df_code)
        except Addfarmer.DoesNotExist:
            return render(request, 'farmer/dashboard.html', {'error': "Farmer not found."})
        
        # Query milk records based on the farmer's DF code and animal type
        cow_morning_records = MilkCollection.objects.filter(farmer=farmer, animal_type='Cow', shift='Morning')
        cow_evening_records = MilkCollection.objects.filter(farmer=farmer, animal_type='Cow', shift='Evening')
        buffalo_morning_records = MilkCollection.objects.filter(farmer=farmer, animal_type='Buffalo', shift='Morning')
        buffalo_evening_records = MilkCollection.objects.filter(farmer=farmer, animal_type='Buffalo', shift='Evening')
        
        # Aggregate data (such as total amount, avg fat, etc.) for rendering
        cow_total_amount = sum(record.amount for record in cow_morning_records) + sum(record.amount for record in cow_evening_records)
        buffalo_total_amount = sum(record.amount for record in buffalo_morning_records) + sum(record.amount for record in buffalo_evening_records)
        total_amount=cow_total_amount+buffalo_total_amount
        # Pass the context to the template
        context = {
            'farmer': farmer,
            'cow_morning_records': cow_morning_records,
            'cow_evening_records': cow_evening_records,
            'buffalo_morning_records': buffalo_morning_records,
            'buffalo_evening_records': buffalo_evening_records,
            'cow_total_amount': cow_total_amount,
            'buffalo_total_amount': buffalo_total_amount,
            'total_amount':total_amount
        }
        
        return render(request, 'generate_report.html', context)
    
    return render(request, 'generate_report.html')


def add_feed(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')
        animal_type = request.POST.get('animal_type')
        price = request.POST.get('price')
        available_stock = request.POST.get('available_stock')
        image = request.FILES.get('image')  # 👈 Handle uploaded file

        Cattlefeed.objects.create(
            name=name,
            description=description,
            animal_type=animal_type,
            price=price,
            available_stock=available_stock,
            image=image
        )
        messages.success(request, "✅ Feed product added successfully!")
        return redirect('add_feeds')

    return render(request, 'add_feeds.html')
def feed_list(request):
    feeds=Cattlefeed.objects.all()
    return render(request,'feed_list.html',{'feeds':feeds})
def orders(request):
    orders = FeedOrder.objects.all().order_by('-ordered_at')
    return render(request, 'orders.html', {'orders': orders})
def mark_as_delivered(request, order_id):
    order = get_object_or_404(FeedOrder, id=order_id)
    order.is_delivered = True
    order.save()
    return redirect('orders') 
def get_muster_dates(period, month, year):
    if period == "1-10":
        return date(year, month, 1), date(year, month, 10)
    elif period == "11-20":
        return date(year, month, 11), date(year, month, 20)
    else:
        last_day = calendar.monthrange(year, month)[1]
        return date(year, month, 21), date(year, month, last_day)

def muster_summary_view(request):
    period = request.GET.get("period", "1-10")
    today = date.today()
    start_date, end_date = get_muster_dates(period, today.month, today.year)

    farmers = Addfarmer.objects.all()
    summary = []

    for farmer in farmers:
        milk_entries = MilkCollection.objects.filter(
            farmer=farmer,
            date__range=(start_date, end_date)
        )

        if milk_entries.exists():
            total_milk = milk_entries.aggregate(Sum("litre"))["litre__sum"] or 0
            avg_fat = milk_entries.aggregate(Avg("fat"))["fat__avg"] or 0
            avg_rate = milk_entries.aggregate(Avg("rate"))["rate__avg"] or 0
            total_amount = milk_entries.aggregate(Sum("amount"))["amount__sum"] or 0

            summary.append({
                "farmer_name": farmer.farmer_name,
                "avg_fat": round(avg_fat, 2),
                "avg_rate": round(avg_rate, 2),
                "total_milk": round(total_milk, 2),
                "total_amount": round(total_amount, 2)
            })

    return render(request, 'muster_summary.html', {
        "summary": summary,
        "period": period,
        "start_date": start_date,
        "end_date": end_date,
    })
