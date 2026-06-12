from django.db.models import Sum, Q, F
from django.utils.text import slugify

from rest_framework import serializers

from .models import Admin, AdminProfile, Category, Employee, Product, Role, Supplier, ScreenOnboarding
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


class AdminUserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False)
    role_name = serializers.CharField(source="role.role", read_only=True)

    class Meta:
        model = Admin
        fields = ("id", "name", "email", "phone", "password", "status", "role", "role_name", "created_at", "updated_at", "deleted_at")
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


class BaseSoftDeleteSerializer(serializers.ModelSerializer):
    class Meta:
        # Must be a tuple (not a string like "__all__") because child serializers
        # concatenate extra fields using + (...,).
        fields = (
            "id",
            "created_at",
            "updated_at",
            "deleted_at",
            "name",
            "slug",
            "permission",
            "role",
            "email",
            "phone",
            "status",
            "is_admin",
            "availability",
            "order_value",
            "quantity",
            "reorder_level",
            "category",
            "supplier",
            "assigned_employee",
            "image",
        )
        read_only_fields = ("id", "created_at", "updated_at", "deleted_at")


class CategorySerializer(BaseSoftDeleteSerializer):
    slug = serializers.SlugField(required=False, allow_blank=True)

    class Meta(BaseSoftDeleteSerializer.Meta):
        model = Category

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

class SupplierSerializer(BaseSoftDeleteSerializer):
    class Meta(BaseSoftDeleteSerializer.Meta):
        model = Supplier


class ProductSerializer(BaseSoftDeleteSerializer):
    stock_status = serializers.CharField(read_only=True)
    category_name = serializers.CharField(source="category.name", read_only=True)
    supplier_name = serializers.CharField(source="supplier.name", read_only=True, default=None)

    # Return absolute URLs for images to avoid broken paths
    image_url = serializers.SerializerMethodField(read_only=True)

    class Meta(BaseSoftDeleteSerializer.Meta):
        model = Product
        fields = BaseSoftDeleteSerializer.Meta.fields + (
            "stock_status",
            "category_name",
            "supplier_name",
            "image_url",
        )

    def get_image_url(self, obj):
        request = self.context.get("request")
        if not obj.image:
            return None
        url = obj.image.url
        if request is not None:
            return request.build_absolute_uri(url)
        return url



class EmployeeSerializer(BaseSoftDeleteSerializer):
    class Meta(BaseSoftDeleteSerializer.Meta):
        model = Employee

class AdminProfileSerializer(BaseSoftDeleteSerializer):
    class Meta(BaseSoftDeleteSerializer.Meta):
        model = AdminProfile


class ScreenOnboardingSerializer(BaseSoftDeleteSerializer):
    class Meta(BaseSoftDeleteSerializer.Meta):
        model = ScreenOnboarding

    image = serializers.ImageField(allow_null=True, required=False)

class DashboardSerializer(serializers.Serializer):
    total_sales = serializers.DecimalField(max_digits=12, decimal_places=2)
    total_revenue = serializers.DecimalField(max_digits=12, decimal_places=2)
    active_orders = serializers.IntegerField()
    cancel_orders = serializers.IntegerField()
    categories = serializers.IntegerField()
    products = serializers.IntegerField()
    low_stock = serializers.IntegerField()
    available_employees = serializers.IntegerField()

    @staticmethod
    def from_metrics():
        orders = Order.objects.filter(deleted_at__isnull=True)
        return {
            "total_sales": orders.aggregate(v=Sum("order_value"))["v"] or 0,
            "total_revenue": orders.exclude(status="cancelled").aggregate(v=Sum("order_value"))["v"] or 0,
            "active_orders": orders.exclude(status="cancelled").count(),
            "cancel_orders": orders.filter(status="cancelled").count(),
            "categories": Category.objects.filter(deleted_at__isnull=True).count(),
            "products": Product.objects.filter(deleted_at__isnull=True).count(),
            "low_stock": Product.objects.filter(deleted_at__isnull=True).filter(
                Q(quantity=0) | Q(quantity__lte=F("reorder_level"))
            ).count(),
            "available_employees": Employee.objects.filter(deleted_at__isnull=True, availability="available").count(),
        }
