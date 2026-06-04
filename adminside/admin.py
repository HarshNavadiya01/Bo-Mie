from django.contrib import admin

# Register your models here.
from .models import Role, Admin, Category, Supplier, Product, AdminProfile, Employee

admin.site.register(Role)
admin.site.register(Admin)
admin.site.register(Category)
admin.site.register(Supplier)
admin.site.register(Product)
admin.site.register(AdminProfile)
admin.site.register(Employee)
