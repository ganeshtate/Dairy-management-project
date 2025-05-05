from django.db import models
from datetime import date
from phonenumber_field.modelfields import PhoneNumberField
from django.contrib.auth.models import User
    



class Addfarmer(models.Model):
    df_code      = models.CharField(max_length=10, unique=True)
    farmer_name  = models.CharField(max_length=100, unique=True)
    date         = models.DateField()
    address = models.TextField(blank=True, null=True)  
    contact = PhoneNumberField(region='IN') 

    def __str__(self):
        return f"{self.df_code} - {self.farmer_name}"





class MilkCollection(models.Model):
    SHIFT_CHOICES = (
        ('morning', 'Morning'),
        ('evening', 'Evening'),
    )
    
    SESSION_CHOICES = (
        ('morning', 'Morning'),
        ('evening', 'Evening'),
    )

    ANIMAL_TYPE_CHOICES = (
        ('cow', 'Cow'),
        ('buffalo', 'Buffalo'),
    )
    animal_type = models.CharField(max_length=10, choices=ANIMAL_TYPE_CHOICES, default='cow')  
    session = models.CharField(max_length=10, choices=SESSION_CHOICES, default='morning')
    farmer = models.ForeignKey(Addfarmer, on_delete=models.CASCADE)
    farmer_name = models.CharField(max_length=100, blank=True)
    df_code = models.CharField(max_length=10, blank=True)
    fat = models.FloatField()
    snf = models.FloatField()
    degree = models.FloatField()
    litre = models.FloatField()
    rate = models.FloatField(blank=True, null=True)
    amount = models.FloatField()
    date = models.DateField(default=date.today)
    shift = models.CharField(max_length=10, choices=SHIFT_CHOICES, default='morning')
    feed_deduction = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    time_of_day = models.CharField(max_length=10, choices=[('morning', 'Morning'), ('evening', 'Evening')])
    # Denormalized fields
   

    def __str__(self):
        return f"{self.farmer_name} - {self.date} ({self.shift}) [{self.animal_type}]"

    def save(self, *args, **kwargs):
        is_new = self._state.adding  # Check if this is a new entry

        # Denormalized fields
        self.farmer_name = self.farmer.farmer_name
        self.df_code = self.farmer.df_code

        # Calculate rate and amount
        self.rate = self.calculate_rate()
        self.amount = self.rate * self.litre

        # Save the record first
        super(MilkCollection, self).save(*args, **kwargs)


    def calculate_rate(self):
        # Example logic to calculate the rate (adjust as needed based on your rate logic)
        rate = (float(self.snf) * 2) + (float(self.fat) * 5) + (float(self.degree) * 0.5)
        return rate
# models.py
class Cattlefeed(models.Model):
    ANIMAL_CHOICES = (
        ('cow', 'Cow'),
        ('buffalo', 'Buffalo'),
        ('both', 'Both'),
    )
    image=models.ImageField(upload_to='feed_images/', blank=True, null=True)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    animal_type = models.CharField(max_length=10, choices=ANIMAL_CHOICES, default='both')
    price = models.DecimalField(max_digits=7, decimal_places=2)
    available_stock = models.PositiveIntegerField()
    added_on = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
class FeedOrder(models.Model):
    farmer = models.ForeignKey(Addfarmer, on_delete=models.CASCADE)
    product = models.ForeignKey(Cattlefeed, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    total_price = models.DecimalField(max_digits=8, decimal_places=2)
    ordered_at = models.DateTimeField(auto_now_add=True)
    is_delivered = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        self.total_price = self.product.price * self.quantity
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.farmer.farmer_name} ordered {self.quantity} x {self.product.name}"
