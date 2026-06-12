from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    AdminChangePasswordAPIView,
    AdminForgotPasswordAPIView,
    AdminLoginAPIView,
    AdminLogoutAPIView,
    AdminTemplateView,
    AdminLoginTemplateView,
    AdminTokenRefreshAPIView,
    AdminUserViewSet,
    ScreenOnboardingViewSet,
    EmployeeViewSet,
    AmenityViewSet,
    StoreViewSet,
    CategoryViewSet,
    DashboardMetricsAPIView,
    EmployeeViewSet,
    ProductViewSet,
    RoleView,
    SupplierViewSet,
    SubCategoryViewSet
)

router = DefaultRouter()
router.register(r"role", RoleView, basename="role")
router.register(r"stores", StoreViewSet, basename="stores")
router.register(r"admins", AdminUserViewSet, basename="admins")
router.register(r"products", ProductViewSet, basename="products")
router.register(r"amenities", AmenityViewSet, basename="amenities")
router.register(r"suppliers", SupplierViewSet, basename="suppliers")
router.register(r"employees", EmployeeViewSet, basename="employees")
# router.register(r"profiles", AdminProfileViewSet, basename="profiles")
router.register(r"categories", CategoryViewSet, basename="categories")
router.register(r"sub-categories", SubCategoryViewSet, basename="sub-categories")
router.register(r"screen-onboarding", ScreenOnboardingViewSet, basename="screen-onboarding")


urlpatterns = [
    path("manage-roles/", include(router.urls)),

    # Dashboard metrics - two paths for compatibility
    path("dashboard/", DashboardMetricsAPIView.as_view(), name="dashboard-metrics"),
    path("dashboard/metrics/", DashboardMetricsAPIView.as_view(), name="dashboard-metrics-v2"),

    # Auth
    path("auth/login/", AdminLoginAPIView.as_view(), name="admin-login"),
    path("auth/refresh/", AdminTokenRefreshAPIView.as_view(), name="admin-refresh-token"),
    path("auth/logout/", AdminLogoutAPIView.as_view(), name="admin-logout"),
    path("auth/forgot-password/", AdminForgotPasswordAPIView.as_view(), name="admin-forgot-password"),
    path("auth/change-password/", AdminChangePasswordAPIView.as_view(), name="admin-change-password"),

    # UI pages
    path("login/", AdminLoginTemplateView.as_view(), name="admin-ui-login"),
    path("ui/", AdminTemplateView.as_view(), {"page": "dashboard"}, name="admin-ui"),
    path("ui/dashboard/", AdminTemplateView.as_view(), {"page": "dashboard"}, name="admin-ui-dashboard"),
    path("ui/<str:page>/", AdminTemplateView.as_view(), name="admin-ui-page"),
]
