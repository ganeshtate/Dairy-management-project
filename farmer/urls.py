from django.urls import path
from .views import *

urlpatterns = [
    path('login/', login, name='login'),
    path('logout/', logout, name='logout'),
    path('dashboard/', dashboard, name='dashboard'),

    path('products/', products, name='products'),
    path('order/<int:product_id>/', place_order, name='place_order'),


    
]
