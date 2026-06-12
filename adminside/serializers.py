import json

from django.db.models import Sum, Q, F
from django.utils.text import slugify

from rest_framework import serializers

from .models import (Admin, AdminProfile, Category, Employee, Product,
                     Role, ScreenOnboarding, SubCategory, Supplier,
                     Amenity, Store)
from userside.models import Order



class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = "__all__"
        read_only_fields = ("id", "created_at", "updated_at", "deleted_at")

class RoleListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = ("id", "role", "permission", "is_admin")

class AdminProfileSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False)
    role_name = serializers.CharField(source="role.role", read_only=True)

    class Meta:
        model = Admin
        fields = ("id", "name", "email", "country_code", "phone", "password", "status", "role", "role_name", "created_at", "updated_at", "deleted_at")
        read_only_fields = ("id", "created_at", "updated_at", "deleted_at")

    def create(self, validated_data):
        password = validated_data.pop("password", None)
        admin = Admin(**validated_data)
        if password:
            admin.set_password(password)
        admin.save()
        return admin

    def update(self, instance, validated_data):
        password = validated_data.pop("password", None)
        for attr, val in validated_data.items():
            setattr(instance, attr, val)
        if password:
            instance.set_password(password)
        instance.save()
        return instance

class AdminLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()

class AdminForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()

class AdminChangePasswordSerializer(serializers.Serializer):
    password = serializers.CharField()
    new_password = serializers.CharField()
    confirm_password = serializers.CharField()

class ImageUrlMixin(serializers.Serializer):
    image_url = serializers.SerializerMethodField(read_only=True)

    def get_image_url(self, obj):
        if not getattr(obj, "image", None):
            return None
        request = self.context.get("request")
        url = obj.image.url
        return request.build_absolute_uri(url) if request else url

    def _delete_replaced_image(self, instance, validated_data):
        old_image = getattr(instance, "image", None)
        new_image = validated_data.get("image")
        if old_image and new_image and old_image.name != getattr(new_image, "name", None):
            old_image.delete(save=False)

    def update(self, instance, validated_data):
        self._delete_replaced_image(instance, validated_data)
        return super().update(instance, validated_data)

class CategorySerializer(ImageUrlMixin, serializers.ModelSerializer):
    slug = serializers.SlugField(required=False, allow_blank=True)
    image = serializers.ImageField(allow_null=True, required=False)

    class Meta:
        model = Category
        fields = (
            "id", "name", "slug", "description", "image", "image_url", "is_active",
            "created_at", "updated_at", "deleted_at",
        )
        read_only_fields = ("id", "image_url", "created_at", "updated_at", "deleted_at")

    def _build_unique_slug(self, name, instance=None):
        base_slug = slugify(name) or "category"
        slug = base_slug
        suffix = 2
        qs = Category.objects.all()
        if instance:
            qs = qs.exclude(pk=instance.pk)
        while qs.filter(slug=slug).exists():
            slug = f"{base_slug}-{suffix}"
            suffix += 1
        return slug

    def validate_slug(self, value):
        return slugify(value) if value else value

    def create(self, validated_data):
        if not validated_data.get("slug"):
            validated_data["slug"] = self._build_unique_slug(validated_data.get("name", "category"))
        return super().create(validated_data)

    def update(self, instance, validated_data):
        if "name" in validated_data and not validated_data.get("slug"):
            validated_data["slug"] = self._build_unique_slug(validated_data["name"], instance=instance)
        return super().update(instance, validated_data)

class SubCategorySerializer(ImageUrlMixin, serializers.ModelSerializer):
    parent_name = serializers.CharField(source="parent.name", read_only=True)
    is_active = serializers.BooleanField(required=False, write_only=True)
    image = serializers.ImageField(allow_null=True, required=False)

    class Meta:
        model = SubCategory
        fields = (
            "id", "parent", "parent_name", "name", "image", "image_url", "display_order",
            "status", "is_active", "created_at", "updated_at", "deleted_at",
        )
        read_only_fields = ("id", "parent_name", "image_url", "created_at", "updated_at", "deleted_at")

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["is_active"] = instance.status == "active"
        return data

    def _normalize_status(self, validated_data):
        if "is_active" in validated_data:
            validated_data["status"] = "active" if validated_data.pop("is_active") else "inactive"
        elif "status" in validated_data:
            validated_data["status"] = "active" if str(validated_data["status"]).lower() == "active" else "inactive"
        return validated_data

    def create(self, validated_data):
        return super().create(self._normalize_status(validated_data))

    def update(self, instance, validated_data):
        return super().update(instance, self._normalize_status(validated_data))

class SupplierSerializer(serializers.ModelSerializer):
    class Meta:
        model = Supplier
        fields = "__all__"
        read_only_fields = ("id", "created_at", "updated_at", "deleted_at")
        

class AmenitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Amenity
        fields = ("id", "name", "created_at", "updated_at", "deleted_at")
        read_only_fields = ("id", "created_at", "updated_at", "deleted_at")


class StoreSerializer(ImageUrlMixin, serializers.ModelSerializer):
    image = serializers.ImageField(allow_null=True, required=False)
    amenities = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Amenity.objects.filter(deleted_at__isnull=True), required=False
    )
    amenity_names = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Store
        fields = (
            "id", "name", "address", "city", "latitude", "longitude", "phone",
            "image", "image_url", "is_active", "supports_takeaway", "supports_dine_in",
            "amenities", "amenity_names", "created_at", "updated_at", "deleted_at",
        )
        read_only_fields = ("id", "image_url", "amenity_names", "created_at", "updated_at", "deleted_at")
        extra_kwargs = {
            "name": {"error_messages": {"blank": "Store name is required.", "required": "Store name is required."}},
            "address": {"error_messages": {"blank": "Address is required.", "required": "Address is required."}},
            "city": {"error_messages": {"blank": "City is required.", "required": "City is required."}},
            "phone": {"error_messages": {"blank": "Phone number is required.", "required": "Phone number is required."}},
        }

    def get_amenity_names(self, obj):
        return [amenity.name for amenity in obj.amenities.filter(deleted_at__isnull=True)]

class ProductSerializer(ImageUrlMixin, serializers.ModelSerializer):
    stock_status = serializers.CharField(read_only=True)
    sub_category_name = serializers.CharField(source="sub_category.name", read_only=True, default=None)
    category = serializers.IntegerField(source="sub_category.parent_id", read_only=True)
    category_name = serializers.CharField(source="sub_category.parent.name", read_only=True, default=None)
    image = serializers.ImageField(allow_null=True, required=False)

    class Meta:
        model = Product
        fields = (
            "id", "name", "product_id", "sub_category", "sub_category_name", "category", "category_name",
            "buying_price", "quantity", "unit", "reorder_level", "opening_stock", "stock_on_way",
            "image", "image_url", "is_active", "description", "app_rating", "is_vegetarian", "is_catering",
            "warning_label", "allergens", "preparation_time_minutes", "base_price", "nutrition",
            "steps_to_burn", "reward_stars_required", "stock_status", "created_at", "updated_at", "deleted_at",
        )
        read_only_fields = ("id", "category", "category_name", "sub_category_name", "image_url", "stock_status", "created_at", "updated_at", "deleted_at")

    def validate(self, attrs):
        for field in ("allergens", "nutrition"):
            value = attrs.get(field)
            if isinstance(value, str):
                value = value.strip()
                if not value:
                    attrs[field] = None
                    continue
                try:
                    attrs[field] = json.loads(value)
                except json.JSONDecodeError as exc:
                    raise serializers.ValidationError({field: "Enter valid JSON."}) from exc
        return attrs

class EmployeeSerializer(ImageUrlMixin, serializers.ModelSerializer):
    image = serializers.ImageField(allow_null=True, required=False)

    class Meta:
        model = Employee
        fields = (
            "id", "name", "store", "contact_number", "email", "availability",
            "delivered_orders", "image", "image_url", "created_at", "updated_at", "deleted_at",
        )
        read_only_fields = ("id", "image_url", "created_at", "updated_at", "deleted_at")
        extra_kwargs = {"store": {"required": False, "allow_null": True}}

class EmployeeSerializer(ImageUrlMixin, serializers.ModelSerializer):
    image = serializers.ImageField(allow_null=True, required=False)

    class Meta:
        model = Employee
        fields = ("id", "name", "store", "contact_number", "email", "availability", "delivered_orders", "image", "image_url", "created_at", "updated_at", "deleted_at")
        read_only_fields = ("id", "created_at", "updated_at", "deleted_at")

class ScreenOnboardingSerializer(ImageUrlMixin, serializers.ModelSerializer):
    image = serializers.ImageField(allow_null=True, required=False)

    class Meta:
        model = ScreenOnboarding
        fields = ("id", "image", "image_url", "title", "sort_order", "is_active", "created_at", "updated_at", "deleted_at")
        read_only_fields = ("id", "image_url", "created_at", "updated_at", "deleted_at")

class DashboardSerializer(serializers.Serializer):
    total_sales = serializers.DecimalField(max_digits=12, decimal_places=2)
    total_revenue = serializers.DecimalField(max_digits=12, decimal_places=2)
    active_orders = serializers.IntegerField()
    cancel_orders = serializers.IntegerField()
    categories = serializers.IntegerField()
    sub_categories = serializers.IntegerField()
    products = serializers.IntegerField()
    low_stock = serializers.IntegerField()
    available_employees = serializers.IntegerField()

    @staticmethod
    def from_metrics():
        orders = Order.objects.filter(deleted_at__isnull=True)
        products = Product.objects.filter(deleted_at__isnull=True)
        return {
            "total_sales": orders.aggregate(v=Sum("grand_total"))["v"] or 0,
            "total_revenue": orders.exclude(order_status="CANCELED").aggregate(v=Sum("grand_total"))["v"] or 0,
            "active_orders": orders.exclude(order_status="CANCELED").count(),
            "cancel_orders": orders.filter(order_status="CANCELED").count(),
            "categories": Category.objects.filter(deleted_at__isnull=True).count(),
            "sub_categories": SubCategory.objects.filter(deleted_at__isnull=True).count(),
            "products": products.count(),
            "low_stock": products.filter(Q(quantity=0) | Q(quantity__lte=F("reorder_level"))).count(),
            "available_employees": Employee.objects.filter(deleted_at__isnull=True, availability="available").count(),
        }
