from django.contrib import admin

# Register your models here.
from .models import User, UserDeviceToken, Order, OrderItem

admin.site.register(User)
admin.site.register(UserDeviceToken)
admin.site.register(Order)
admin.site.register(OrderItem)