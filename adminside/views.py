from django.contrib.auth.tokens import default_token_generator
from django.db.models import Sum
from django.shortcuts import render
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

from .authentication import AdminJWTAuthentication
from .models import Admin, AdminProfile, Category, Employee, Order, Product, Role, Supplier
from .permissions import HasRolePermission, IsRoleAdmin
from .serializers import (
    AdminChangePasswordSerializer,
    AdminForgotPasswordSerializer,
    AdminLoginSerializer,
    AdminProfileSerializer,
    AdminUserSerializer,
    CategorySerializer,
    DashboardSerializer,
    EmployeeSerializer,
    OrderSerializer,
    ProductSerializer,
    RoleListSerializer,
    RoleSerializer,
    SupplierSerializer,
)


class SoftDeleteModelViewSet(ModelViewSet):
    def get_queryset(self):
        qs = self.queryset
        if self.request.query_params.get("include_deleted") != "true":
            qs = qs.filter(deleted_at__isnull=True)
        return qs

    def perform_destroy(self, instance):
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
    serializer_class = AdminUserSerializer
    authentication_classes = [AdminJWTAuthentication]
    permission_classes = [IsAuthenticated, HasRolePermission]


class CategoryViewSet(SoftDeleteModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    authentication_classes = [AdminJWTAuthentication]
    permission_classes = [IsAuthenticated]


class SupplierViewSet(SoftDeleteModelViewSet):
    queryset = Supplier.objects.all()
    serializer_class = SupplierSerializer
    authentication_classes = [AdminJWTAuthentication]
    permission_classes = [IsAuthenticated]


class ProductViewSet(SoftDeleteModelViewSet):
    queryset = Product.objects.select_related("category", "supplier")
    serializer_class = ProductSerializer
    authentication_classes = [AdminJWTAuthentication]
    permission_classes = [IsAuthenticated]


class EmployeeViewSet(SoftDeleteModelViewSet):
    queryset = Employee.objects.all()
    serializer_class = EmployeeSerializer
    authentication_classes = [AdminJWTAuthentication]
    permission_classes = [IsAuthenticated]


class OrderViewSet(SoftDeleteModelViewSet):
    queryset = Order.objects.select_related("product", "assigned_employee")
    serializer_class = OrderSerializer
    authentication_classes = [AdminJWTAuthentication]
    permission_classes = [IsAuthenticated]


class AdminProfileViewSet(SoftDeleteModelViewSet):
    queryset = AdminProfile.objects.select_related("admin")
    serializer_class = AdminProfileSerializer
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
            admin = Admin.objects.select_related("role").get(email=serializer.validated_data["email"], deleted_at__isnull=True, status=True)
        except Admin.DoesNotExist:
            return Response({"detail": "Invalid credentials."}, status=status.HTTP_401_UNAUTHORIZED)
        if not admin.verify_password(serializer.validated_data["password"]):
            return Response({"detail": "Invalid credentials."}, status=status.HTTP_401_UNAUTHORIZED)
        refresh = RefreshToken()
        refresh["admin_id"] = admin.id
        refresh["role_id"] = admin.role_id
        refresh["is_admin"] = admin.role.is_admin
        return Response({"access": str(refresh.access_token), "refresh": str(refresh), "admin": AdminUserSerializer(admin).data})


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
        return Response({"uid": urlsafe_base64_encode(force_bytes(admin.pk)), "reset_token": default_token_generator.make_token(admin)})


class AdminChangePasswordAPIView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        serializer = AdminChangePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response({"detail": "Password changed successfully."})


class AdminTemplateView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request, page="dashboard"):
        return render(request, "adminside/index.html", {"page": page})


AdminView = AdminUserViewSet