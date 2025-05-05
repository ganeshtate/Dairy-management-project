from django.contrib import admin
from django.urls import path,include
from .views import *
urlpatterns = [
   path('home/',gethomepage,name='home'),
   path('farmer/',farmer,name='farmer'),
   path('add-farmer/',add_farmer,name='add_farmer'),
   path('show_farmers/',show_farmers,name='show_farmers'),
   path('delete/', delete, name='delete'),
   path('edit_farmer/',edit_farmer,name='edit_farmer'),
   path('update_farmer',update_farmer,name='update_farmer'),
   path('collect_milk/',collect_milk,name='collect_milk'),
   path('generate-report/',generate_report, name='generate_report'),
   path('add_feeds/',add_feed,name='add_feeds'),
   path('feed_list',feed_list,name='feed_list'),
   path('orders/', orders, name='orders'),
   path('mark-as-delivered/<int:order_id>/', mark_as_delivered, name='mark_as_delivered'),
   path('bill/',muster_summary_view,name='bill')
]