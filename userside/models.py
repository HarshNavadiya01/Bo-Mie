from django.db import models
from adminside.models import BaseModel, Store, Product


class UserDeviceToken(BaseModel):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(
        "User", on_delete=models.CASCADE, db_column="user_id",
        null=True, blank=True,
    )
    device_token = models.CharField(max_length=1000, unique=True, db_index=True)
    platform = models.CharField(max_length=255)  # "android" / "ios"
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "user_device_tokens"


# ==========================================================================
# SETTINGS  (app/models/settings.py)
# ==========================================================================
# class AppSetting(BaseModel):
#     id = models.AutoField(primary_key=True)
#     tax_percentage = models.FloatField(default=15.0)
#     terms_url = models.CharField(max_length=1000, null=True, blank=True)
#     updated_at = models.DateTimeField(auto_now=True)

#     class Meta:
#         db_table = "app_settings"


# class FAQ(BaseModel):
#     id = models.AutoField(primary_key=True)
#     question = models.CharField(max_length=1000)
#     answer = models.CharField(max_length=2000)
#     display_order = models.IntegerField(default=0)
#     is_active = models.BooleanField(default=True)
#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)

#     class Meta:
#         db_table = "settings_faq"


# ==========================================================================
# USER  (app/models/user.py)
# ==========================================================================
class User(BaseModel):
    id = models.AutoField(primary_key=True)
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    gender = models.CharField(max_length=255)
    date_of_birth = models.DateField()

    country_code = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=255, unique=True, db_index=True)
    email = models.CharField(max_length=255, null=True, blank=True)
    acquisition_source = models.CharField(max_length=255, null=True, blank=True)

    # Section 16: identity & phone-change flow
    temporary_phone_number = models.CharField(max_length=255, null=True, blank=True)

    # Section 16: marketing & privacy consents
    email_marketing_opt_in = models.BooleanField(default=True)
    personalization_opt_in = models.BooleanField(default=True)

    # Loyalty & tiers
    royale_points_balance = models.FloatField(default=0.0)
    annual_status_tracker = models.FloatField(default=0.0)
    tier_status = models.CharField(max_length=255, default="Standard")
    show_gold_unlock_popup = models.BooleanField(default=False)

    # Navigation gatekeeper
    selected_store = models.ForeignKey(
        Store, on_delete=models.SET_NULL, db_column="selected_store_id",
        null=True, blank=True,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "users"

    # DRF's IsAuthenticated checks ``is_authenticated``; our token auth only
    # ever returns a real User row, so this is always True for resolved users.
    @property
    def is_authenticated(self):
        return True


class UserOTPVerification(BaseModel):
    id = models.AutoField(primary_key=True)
    country_code = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=255)
    otp_code = models.CharField(max_length=255)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "otp_verifications"



# class UserPaymentMethod(BaseModel):
#     id = models.AutoField(primary_key=True)
#     user = models.ForeignKey(
#         User, on_delete=models.CASCADE, db_column="user_id",
#         related_name="payment_methods",
#     )
#     payment_token = models.CharField(max_length=1000)
#     brand = models.CharField(max_length=255, null=True, blank=True)
#     last4 = models.CharField(max_length=255, null=True, blank=True)
#     expiry = models.CharField(max_length=255, null=True, blank=True)
#     is_default = models.BooleanField(default=False)
#     created_at = models.DateTimeField(auto_now_add=True)

#     class Meta:
#         db_table = "user_payment_methods"


# ==========================================================================
# ORDER  (app/models/order.py)
# ==========================================================================
class Order(BaseModel):
    id = models.AutoField(primary_key=True)
    order_number = models.CharField(max_length=255, unique=True, db_index=True, null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, db_column="user_id", null=True, blank=True)
    store = models.ForeignKey(Store, on_delete=models.SET_NULL, db_column="store_id", null=True, blank=True)

    display_order_number = models.CharField(max_length=255, unique=True, db_index=True, null=True, blank=True)
    master_order_id = models.CharField(max_length=255, unique=True, db_index=True, null=True, blank=True)

    order_status = models.CharField(max_length=255, default="PENDING")  # PENDING, PREPARING, COMPLETED, CANCELED, SCHEDULED
    dynamic_eta = models.CharField(max_length=255, null=True, blank=True)

    order_type = models.CharField(max_length=255, default="TAKEAWAY")  # TAKEAWAY, DINE_IN, CATERING
    pickup_date = models.DateField(null=True, blank=True)
    pickup_time = models.CharField(max_length=255, null=True, blank=True)
    pickup_date_time = models.DateTimeField(null=True, blank=True)

    table_number = models.CharField(max_length=255, null=True, blank=True)

    grand_total = models.FloatField(default=0.0)
    previous_payment = models.FloatField(default=0.0)
    payment_method = models.CharField(max_length=255, null=True, blank=True)
    payment_status = models.CharField(max_length=255, default="PAID")  # PAID / UNPAID
    is_editing = models.BooleanField(default=False)

    points_earned = models.FloatField(default=0.0)
    points_status = models.CharField(max_length=255, default="PENDING")  # PENDING, AWARDED
    points_awarded_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "orders"


class OrderItem(BaseModel):
    id = models.AutoField(primary_key=True)
    order = models.ForeignKey(
        Order, on_delete=models.CASCADE, db_column="order_id",
        related_name="items", null=True, blank=True,
    )
    product = models.ForeignKey(
        Product, on_delete=models.SET_NULL, db_column="product_id",
        null=True, blank=True,
    )
    product_title = models.CharField(max_length=255, null=True, blank=True)
    quantity = models.IntegerField(default=1)

    base_price = models.FloatField(default=0.0)
    type1_total = models.FloatField(default=0.0)
    type2_total = models.FloatField(default=0.0)
    unit_final_price = models.FloatField(default=0.0)
    row_total = models.FloatField(default=0.0)

    is_reward_applied = models.BooleanField(default=False)
    points_used = models.IntegerField(default=0)
    reward_badge = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        db_table = "order_items"


# ==========================================================================
# SUPPORT  (app/models/support.py)
# ==========================================================================
# class SupportTicket(BaseModel):
#     id = models.AutoField(primary_key=True)
#     user = models.ForeignKey(User, on_delete=models.CASCADE, db_column="user_id", null=True, blank=True)
#     master_order_id = models.CharField(max_length=255)
#     display_order_number = models.CharField(max_length=255)
#     message = models.TextField()
#     status = models.CharField(max_length=255, default="OPEN")
#     created_at = models.DateTimeField(auto_now_add=True)

#     class Meta:
#         db_table = "support_tickets"