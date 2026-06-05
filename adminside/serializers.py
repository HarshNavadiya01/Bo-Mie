from django.db.models import Sum, Q, F
from rest_framework import serializers

from .models import Admin, AdminProfile, Category, Employee, Order, Product, Role, Supplier


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
        fields = "__all__"
        read_only_fields = ("id", "created_at", "updated_at", "deleted_at")


class CategorySerializer(BaseSoftDeleteSerializer):
    class Meta(BaseSoftDeleteSerializer.Meta):
        model = Category


class SupplierSerializer(BaseSoftDeleteSerializer):
    class Meta(BaseSoftDeleteSerializer.Meta):
        model = Supplier


class ProductSerializer(BaseSoftDeleteSerializer):
    stock_status = serializers.CharField(read_only=True)
    category_name = serializers.CharField(source="category.name", read_only=True)
    supplier_name = serializers.CharField(source="supplier.name", read_only=True, default=None)

    class Meta(BaseSoftDeleteSerializer.Meta):
        model = Product


class EmployeeSerializer(BaseSoftDeleteSerializer):
    class Meta(BaseSoftDeleteSerializer.Meta):
        model = Employee


class OrderSerializer(BaseSoftDeleteSerializer):
    product_name = serializers.CharField(source="product.name", read_only=True)
    employee_name = serializers.CharField(source="assigned_employee.name", read_only=True, default=None)

    class Meta(BaseSoftDeleteSerializer.Meta):
        model = Order


class AdminProfileSerializer(BaseSoftDeleteSerializer):
    class Meta(BaseSoftDeleteSerializer.Meta):
        model = AdminProfile


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
