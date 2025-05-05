from django.contrib import admin
from .models import Addfarmer
from .models import MilkCollection
from .models import Cattlefeed
from .models import FeedOrder
# Register your models here.
admin.site.register(Addfarmer)
admin.site.register(MilkCollection)
admin.site.register(Cattlefeed)
admin.site.register(FeedOrder)

