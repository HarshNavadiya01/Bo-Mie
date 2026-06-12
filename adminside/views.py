from django.contrib.auth.tokens import default_token_generator
from django.db.models import Sum
from django.shortcuts import render, redirect
from django.utils import timezone
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from rest_framework_simplejwt.tokens import RefreshToken, TokenError
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser

from .authentication import AdminJWTAuthentication
from .models import (Admin, AdminProfile, Category, Employee, Product, Role, Supplier,
                     ScreenOnboarding, SubCategory, Store, Amenity)

from .permissions import HasRolePermission, IsRoleAdmin
from .serializers import (

    AdminChangePasswordSerializer,
    AdminForgotPasswordSerializer,
    AdminLoginSerializer,
    AdminProfileSerializer,
    CategorySerializer,
    DashboardSerializer,
    EmployeeSerializer,
    ProductSerializer,
    RoleListSerializer,
    RoleSerializer,
    ScreenOnboardingSerializer,
    SupplierSerializer,
    SubCategorySerializer,
    AmenitySerializer,
    StoreSerializer,
)


# Page → template mapping
PAGE_TEMPLATES = {
    "dashboard": "dashboard/dashboard.html",
    "inventory": "dashboard/inventory.html",
    "reports":   "dashboard/reports.html",
    "employees": "dashboard/employee.html",
    "orders":    "dashboard/orders.html",
    "settings":  "dashboard/settings.html",
    "stores":    "dashboard/stores.html",
}


class SoftDeleteModelViewSet(ModelViewSet):
    parser_classes = [JSONParser, MultiPartParser, FormParser]

    def get_queryset(self):
        qs = self.queryset
        if self.request.query_params.get("include_deleted") != "true":
            qs = qs.filter(deleted_at__isnull=True)
        return qs

    def perform_destroy(self, instance):
        image = getattr(instance, "image", None)
        if image:
            image.delete(save=False)
        instance.deleted_at = timezone.now()
        instance.save(update_fields=["deleted_at", "updated_at"])



class RoleView(SoftDeleteModelViewSet):
    queryset = Role.objects.all()
    serializer_class = RoleSerializer
    authentication_classes = [AdminJWTAuthentication]
    permission_classes = [IsAuthenticated, IsRoleAdmin]

    def get_serializer_class(self):
        return RoleListSerializer if self.action == "list" else RoleSerializer


class AdminUserViewSet(SoftDeleteModelViewSet):
    queryset = Admin.objects.select_related("role")
    serializer_class = AdminProfileSerializer
    authentication_classes = [AdminJWTAuthentication]
    permission_classes = [IsAuthenticated, HasRolePermission]


class CategoryViewSet(SoftDeleteModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    authentication_classes = [AdminJWTAuthentication]
    permission_classes = [IsAuthenticated]

    @action(detail=True, methods=["patch"], url_path="toggle-status")
    def toggle_status(self, request, pk=None):
        category = self.get_object()
        category.is_active = not category.is_active
        category.save(update_fields=["is_active", "updated_at"])
        return Response(self.get_serializer(category).data)


class SubCategoryViewSet(SoftDeleteModelViewSet):
    queryset = SubCategory.objects.select_related("parent")
    serializer_class = SubCategorySerializer
    authentication_classes = [AdminJWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = super().get_queryset()
        parent = self.request.query_params.get("parent") or self.request.query_params.get("category")
        if parent:
            qs = qs.filter(parent_id=parent)
        status_value = self.request.query_params.get("status")
        if status_value:
            qs = qs.filter(status=status_value)
        return qs

    @action(detail=True, methods=["patch"], url_path="toggle-status")
    def toggle_status(self, request, pk=None):
        sub_category = self.get_object()
        sub_category.status = "inactive" if sub_category.status == "active" else "active"
        sub_category.save(update_fields=["status", "updated_at"])
        return Response(self.get_serializer(sub_category).data)


class SupplierViewSet(SoftDeleteModelViewSet):
    queryset = Supplier.objects.all()
    serializer_class = SupplierSerializer
    authentication_classes = [AdminJWTAuthentication]
    permission_classes = [IsAuthenticated]


class AmenityViewSet(SoftDeleteModelViewSet):
    queryset = Amenity.objects.all()
    serializer_class = AmenitySerializer
    authentication_classes = [AdminJWTAuthentication]
    permission_classes = [IsAuthenticated]


class StoreViewSet(SoftDeleteModelViewSet):
    queryset = Store.objects.prefetch_related("amenities")
    serializer_class = StoreSerializer
    authentication_classes = [AdminJWTAuthentication]
    permission_classes = [IsAuthenticated]

    @action(detail=True, methods=["patch"], url_path="toggle-status")
    def toggle_status(self, request, pk=None):
        store = self.get_object()
        store.is_active = not store.is_active
        store.save(update_fields=["is_active", "updated_at"])
        return Response(self.get_serializer(store).data)

class ProductViewSet(SoftDeleteModelViewSet):
    queryset = Product.objects.select_related("sub_category", "sub_category__parent")
    serializer_class = ProductSerializer
    authentication_classes = [AdminJWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = super().get_queryset()
        cat = self.request.query_params.get("category")
        if cat:
            qs = qs.filter(sub_category__parent_id=cat)
        sub_cat = self.request.query_params.get("sub_category")
        if sub_cat:
            qs = qs.filter(sub_category_id=sub_cat)
        return qs



class EmployeeViewSet(SoftDeleteModelViewSet):
    queryset = Employee.objects.all()
    serializer_class = EmployeeSerializer
    authentication_classes = [AdminJWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = super().get_queryset()
        avail = self.request.query_params.get("availability")
        if avail:
            qs = qs.filter(availability=avail)
        return qs

class AdminProfileViewSet(SoftDeleteModelViewSet):
    queryset = AdminProfile.objects.select_related("admin")
    serializer_class = AdminProfileSerializer
    authentication_classes = [AdminJWTAuthentication]
    permission_classes = [IsAuthenticated]


class ScreenOnboardingViewSet(SoftDeleteModelViewSet):
    queryset = ScreenOnboarding.objects.all()
    serializer_class = ScreenOnboardingSerializer
    authentication_classes = [AdminJWTAuthentication]
    permission_classes = [IsAuthenticated]


class DashboardMetricsAPIView(APIView):

    authentication_classes = [AdminJWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        payload = DashboardSerializer.from_metrics()
        return Response(DashboardSerializer(payload).data)


class AdminLoginAPIView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        serializer = AdminLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            admin = Admin.objects.select_related("role").get(
                email=serializer.validated_data["email"],
                deleted_at__isnull=True,
                status=True,
            )
        except Admin.DoesNotExist:
            return Response({"detail": "Invalid credentials."}, status=status.HTTP_401_UNAUTHORIZED)
        if not admin.verify_password(serializer.validated_data["password"]):
            return Response({"detail": "Invalid credentials."}, status=status.HTTP_401_UNAUTHORIZED)
        refresh = RefreshToken()
        refresh["admin_id"] = admin.id
        refresh["role_id"] = admin.role_id
        refresh["is_admin"] = admin.role.is_admin
        return Response({
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "admin": AdminProfileSerializer(admin).data,
        })


class AdminTokenRefreshAPIView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        raw = request.headers.get("Authorization", "")
        token = raw.split(" ", 1)[1].strip() if raw.startswith("Bearer ") else raw.strip()
        serializer = TokenRefreshSerializer(data={"refresh": token})
        serializer.is_valid(raise_exception=True)
        return Response(serializer.validated_data)


class AdminLogoutAPIView(APIView):
    authentication_classes = [AdminJWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        raw = request.headers.get("Authorization", "")
        token = raw.split(" ", 1)[1].strip() if raw.startswith("Bearer ") else raw.strip()
        try:
            RefreshToken(token).blacklist()
        except TokenError:
            return Response({"detail": "Invalid or expired refresh token."}, status=400)
        return Response({"detail": "Logged out successfully."})


class AdminForgotPasswordAPIView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        serializer = AdminForgotPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            admin = Admin.objects.get(email=serializer.validated_data["email"], deleted_at__isnull=True)
        except Admin.DoesNotExist:
            return Response({"detail": "If this email exists, a reset token has been generated."})
        return Response({
            "uid": urlsafe_base64_encode(force_bytes(admin.pk)),
            "reset_token": default_token_generator.make_token(admin),
        })


class AdminChangePasswordAPIView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        serializer = AdminChangePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response({"detail": "Password changed successfully."})


class AdminTemplateView(APIView):
    """
    Serve HTML templates for the admin SPA.
    Auth is handled client-side via JWT in localStorage.
    Django only serves the shell; the JS checks for a valid token.
    """
    authentication_classes = []
    permission_classes = []

    def get(self, request, page="dashboard"):
        template = PAGE_TEMPLATES.get(page, "dashboard/dashboard.html")
        return render(request, template, {"page": page})


AdminView = AdminUserViewSet


class AdminLoginTemplateView(APIView):
    """Public login page - no auth required."""
    authentication_classes = []
    permission_classes = []

    def get(self, request):
        # If already logged in, redirect to dashboard
        return render(request, "authentication/login.html")
