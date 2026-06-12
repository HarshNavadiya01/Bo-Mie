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
    country_code = models.CharField(max_length=25, null=True, blank=True)
    phone = models.CharField(max_length=20, unique=True)
    password = models.CharField(max_length=128)
    status = models.BooleanField(default=True)
    is_admin = models.BooleanField(default=True)
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
    description = models.TextField(blank=True)
    image = models.ImageField(
        upload_to="images/category/",
        null=True,
        blank=True
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "categories"
        ordering = ["name"]

class SubCategory(BaseModel):
    parent = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name="sub_categories"
    )
    name = models.CharField(max_length=255)
    image = models.ImageField(
        upload_to="images/subcategory/",
        null=True,
        blank=True
    )
    status = models.CharField(
        max_length=20,
        default="active"
    )

    class Meta:
        db_table = "sub_categories"

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
    product_id = models.CharField(
        max_length=50,
        unique=True,
        null=True,
        blank=True
    )
    sub_category = models.ForeignKey(SubCategory, on_delete=models.PROTECT,
        related_name="products",
        null=True,
        blank=True
    )
    buying_price = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )
    quantity = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )
    image = models.ImageField(
        upload_to="images/product/",
        null=True,
        blank=True
    )
    is_active = models.BooleanField(default=True)
    description = models.TextField(
        null=True,
        blank=True
    )
    app_rating = models.FloatField(default=0.0)
    is_vegetarian = models.BooleanField(default=False)
    unit = models.CharField(max_length=20, choices=UNIT_CHOICES, default="piece")
    reorder_level = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    opening_stock = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    stock_on_way = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    # --- Catering module fields ---
    is_catering = models.BooleanField(default=False)
    warning_label = models.CharField(
        max_length=255, default="⚠️ Please Order 48 hours in advance"
    )
    allergens = models.JSONField(null=True, blank=True)

    preparation_time_minutes = models.IntegerField(default=0)
    base_price = models.FloatField(default=0.0)
    nutrition = models.JSONField(null=True, blank=True)
    steps_to_burn = models.IntegerField(default=0)
    reward_stars_required = models.IntegerField(default=0)
    class Meta:
        db_table = "products"

    @property
    def stock_status(self):
        if self.quantity == 0:
            return "out_of_stock"
        if self.quantity <= self.reorder_level:
            return "low_stock"
        return "in_stock"

class AdminProfile(BaseModel):
    admin = models.OneToOneField(Admin, on_delete=models.CASCADE, related_name="profile")
    user_id = models.CharField(max_length=80)
    notifications_enabled = models.BooleanField(default=True)
    location_enabled = models.BooleanField(default=False)

class ScreenOnboarding(BaseModel):
    """Images for the onboarding/start screen shown to users in the mobile app."""

    image = models.ImageField(upload_to="images/onboarding/", null=True, blank=True)
    title = models.CharField(max_length=200, blank=True)
    sort_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["sort_order", "id"]
        indexes = [models.Index(fields=["is_active", "sort_order"])]

    def __str__(self):
        return self.title or f"Onboarding #{self.id}"
    
class Amenity(BaseModel):
    name = models.CharField(
        max_length=100,
        unique=True
    )
    class Meta:
        db_table = "amenities"
        ordering = ["name"]

    def __str__(self):
        return self.name

class Store(BaseModel):
    name = models.CharField(max_length=200)
    address = models.TextField()
    city = models.CharField(max_length=100)
    latitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True
    )
    longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True
    )
    phone = models.CharField(max_length=20)
    image = models.ImageField(
        upload_to="stores/",
        null=True,
        blank=True
    )
    is_active = models.BooleanField(default=True)
    supports_takeaway = models.BooleanField(default=False)
    supports_dine_in = models.BooleanField(default=False)
    amenities = models.ManyToManyField(
        Amenity,
        blank=True,
        related_name="stores"
    )
    class Meta:
        db_table = "stores"
        ordering = ["name"]

    def __str__(self):
        return self.name

class StoreOperatingHour(BaseModel):
    DAYS = (
        ("MON", "Monday"),
        ("TUE", "Tuesday"),
        ("WED", "Wednesday"),
        ("THU", "Thursday"),
        ("FRI", "Friday"),
        ("SAT", "Saturday"),
        ("SUN", "Sunday"),
    )
    
    store = models.ForeignKey(
        Store,
        on_delete=models.CASCADE,
        related_name="operating_hours"
    )
    day = models.CharField(
        max_length=3,
        choices=DAYS
    )
    open_time = models.TimeField(
        null=True,
        blank=True
    )

    close_time = models.TimeField(
        null=True,
        blank=True
    )

    is_closed = models.BooleanField(default=False)

    class Meta:
        db_table = "store_operating_hours"

        constraints = [
            models.UniqueConstraint(
                fields=["store", "day"],
                name="unique_store_day"
            )
        ]

        ordering = ["id"]

    def __str__(self):
        return f"{self.store.name} - {self.day}"
    
class Customization(BaseModel):
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, db_column="product_id",
        related_name="customizations", null=True, blank=True,
    )
    type = models.CharField(max_length=255, null=True, blank=True)  # master_variant, visual_addon, stepper, dropdown
    name = models.CharField(max_length=255, null=True, blank=True)
    title = models.CharField(max_length=255, null=True, blank=True)
    price_per_increment = models.FloatField(null=True, blank=True)
    max_limit = models.IntegerField(null=True, blank=True)
    recommend = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        db_table = "customization_blocks"

class CustomizationOption(BaseModel):
    block = models.ForeignKey(
        Customization, on_delete=models.CASCADE, db_column="block_id",
        related_name="options", null=True, blank=True,
    )
    title = models.CharField(max_length=255, null=True, blank=True)
    image = models.CharField(max_length=1000, null=True, blank=True)
    price = models.FloatField(default=0.0)
    nutrition = models.JSONField(null=True, blank=True)
    steps_to_burn = models.IntegerField(null=True, blank=True)
    reward_stars_required = models.IntegerField(null=True, blank=True)

    class Meta:
        db_table = "customization_options"
        
class Employee(BaseModel):
    AVAILABILITY_CHOICES = [("available", "Available"), ("unavailable", "Unavailable")]
    name = models.CharField(max_length=120)
    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name="employees", null=True)
    contact_number = models.CharField(max_length=20)
    email = models.EmailField(unique=True)
    availability = models.CharField(max_length=20, choices=AVAILABILITY_CHOICES, default="available")
    delivered_orders = models.PositiveIntegerField(default=0)
    image = models.ImageField(upload_to="images/employees/", null=True, blank=True)
    