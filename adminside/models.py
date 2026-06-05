from django.db import models
from django.contrib.postgres.fields import ArrayField
from django.contrib.auth.hashers import check_password, make_password


class BaseModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        abstract = True


class Role(BaseModel):
    role = models.CharField(max_length=100, unique=True)
    permission = ArrayField(base_field=models.CharField(max_length=100), default=list, blank=True)
    is_admin = models.BooleanField(default=False)

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return self.role


class Admin(BaseModel):
    name = models.CharField(max_length=120)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, unique=True)
    password = models.CharField(max_length=128)
    status = models.BooleanField(default=True)
    role = models.ForeignKey(Role, on_delete=models.PROTECT, related_name="admins")

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return self.email

    def set_password(self, raw_password):
        self.password = make_password(raw_password)

    def verify_password(self, raw_password):
        return check_password(raw_password, self.password)

    @property
    def is_authenticated(self):
        return True

    @property
    def is_anonymous(self):
        return False


class Category(BaseModel):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(unique=True)
    parent = models.ForeignKey("self", on_delete=models.CASCADE, null=True, blank=True, related_name="children")
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to="categories/", null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]
        indexes = [models.Index(fields=["slug"])]

    def __str__(self):
        return self.name


class Supplier(BaseModel):
    name = models.CharField(max_length=150)
    code = models.CharField(max_length=50, unique=True)
    contact_person = models.CharField(max_length=120, blank=True)
    phone = models.CharField(max_length=20)
    email = models.EmailField(null=True, blank=True)
    address = models.TextField(null=True, blank=True)
    city = models.CharField(max_length=100, null=True, blank=True)
    country = models.CharField(max_length=100, null=True, blank=True)
    tax_number = models.CharField(max_length=50, null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        indexes = [models.Index(fields=["code"]), models.Index(fields=["name"])]

    def __str__(self):
        return f"{self.name} ({self.code})"


class Product(BaseModel):
    UNIT_CHOICES = [
        ("piece", "Piece"),
        ("kg", "Kilogram"),
        ("g", "Gram"),
        ("l", "Liter"),
        ("ml", "Milliliter"),
    ]

    name = models.CharField(max_length=150)
    product_id = models.CharField(max_length=50, unique=True, null=True, blank=True)
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="products")
    buying_price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    unit = models.CharField(max_length=20, choices=UNIT_CHOICES)
    image = models.ImageField(upload_to="./static/images/products/", null=True, blank=True)
    opening_stock = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    stock_on_way = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["id"]
        indexes = [models.Index(fields=["category"]), models.Index(fields=["product_id"])]

    @property
    def stock_status(self):
        if self.quantity == 0:
            return "out_of_stock"
        if self.quantity <= self.reorder_level:
            return "low_stock"
        return "in_stock"


class Employee(BaseModel):
    AVAILABILITY_CHOICES = [("available", "Available"), ("unavailable", "Unavailable")]
    name = models.CharField(max_length=120)
    contact_number = models.CharField(max_length=20)
    email = models.EmailField(unique=True)
    availability = models.CharField(max_length=20, choices=AVAILABILITY_CHOICES, default="available")
    delivered_orders = models.PositiveIntegerField(default=0)
    image = models.ImageField(upload_to="employees/", null=True, blank=True)


class Order(BaseModel):
    STATUS_CHOICES = [
        ("confirmed", "Confirmed"),
        ("out_for_delivery", "Out for delivery"),
        ("cancelled", "Cancelled"),
        ("catering", "Catering"),
    ]
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name="orders")
    quantity = models.PositiveIntegerField(default=1)
    order_value = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default="confirmed")
    assigned_employee = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, blank=True, related_name="orders")


class AdminProfile(BaseModel):
    admin = models.OneToOneField(Admin, on_delete=models.CASCADE, related_name="profile")
    user_id = models.CharField(max_length=80)
    notifications_enabled = models.BooleanField(default=True)
    location_enabled = models.BooleanField(default=False)