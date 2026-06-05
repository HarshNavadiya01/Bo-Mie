# BOandMIE — Project Architecture & File-by-File Functionality

> This document describes what each file in the current repo contributes: responsibilities, key classes/functions, endpoints/templates/JS usage, and how features connect end-to-end.

---

## 1) High-level Overview

This repository is a **Django + Django REST Framework (DRF) + djangorestframework-simplejwt** project.

### Main feature areas
1. **Admin authentication**
   - Login via email/password → JWT access + refresh tokens
   - Token refresh endpoint
   - Logout (refresh token blacklist)
   - Forgot password and change password endpoints (currently token generation/placeholder change response)

2. **Role-based authorization**
   - Roles stored in DB with an `is_admin` boolean and a list of permission codes (`permission` as an ArrayField)
   - Permissions enforced via custom DRF permission classes

3. **CRUD APIs for business entities**
   - Role, Admin, Category, Supplier, Product, Employee, Order, AdminProfile
   - Supports **soft-delete** via `deleted_at`; API hides deleted rows by default

4. **Admin dashboard UI**
   - Server-rendered templates (sidebar/navbar/layout)
   - Dashboard metrics endpoint consumed by dashboard JS

---

## 2) Dependencies (requirements.txt)

### File: `requirements.txt`
- Declares runtime and development dependencies.
- (Not fully readable in earlier extraction due to encoding, but it includes Django, Django REST Framework, simplejwt, psycopg2-binary, etc.)

---

## 3) Django Project Configuration

### File: `manage.py`
- Standard Django entry point.
- Sets `DJANGO_SETTINGS_MODULE='BOandMIE.settings'` and runs `execute_from_command_line`.

### File: `BOandMIE/settings.py`
- Core settings for the Django project.

Key settings:
- **Installed apps**
  - `adminside`
  - `rest_framework`
  - `rest_framework_simplejwt`
  - Django admin/auth/contenttypes/sessions/staticfiles

- **REST_FRAMEWORK**
  - `DEFAULT_PERMISSION_CLASSES`: `IsAuthenticated`
  - `DEFAULT_AUTHENTICATION_CLASSES`: `adminside.authentication.AdminJWTAuthentication`
  - Pagination settings

- **SIMPLE_JWT**
  - Access lifetime: 15 minutes
  - Refresh lifetime: 7 days
  - Rotates refresh tokens
  - Blacklist after rotation

- **Database**
  - PostgreSQL backend
  - Database name: `BoandMie`
  - Host: `localhost`, Port: `5432`

- **Templates**
  - Uses `DIRS: [BASE_DIR / 'templates']`
  - Also supports `APP_DIRS=True`

- **Static files**
  - `STATIC_URL = 'static/'`

---

### File: `BOandMIE/urls.py`
Routes project URLs.

Endpoints:
- `platform-admin/` → Django admin site (`admin.site.urls`)
- `api/v1/admin/` → includes `adminside.urls`
- If DEBUG: serves media via `static(settings.MEDIA_URL, ...)` (note: `MEDIA_URL`/`MEDIA_ROOT` not shown in extracted snippet)

---

### File: `BOandMIE/asgi.py` / `BOandMIE/wsgi.py`
- Standard Django ASGI/WSGI entrypoints.

---

## 4) Application: `adminside`

### File: `adminside/apps.py`
- Defines Django app config.
- `name = 'adminside'`

---

### File: `adminside/models.py`
Defines the database models used by the system.

#### 4.1 `BaseModel` (abstract)
Fields:
- `created_at` (`auto_now_add=True`)
- `updated_at` (`auto_now=True`)
- `deleted_at` (`null=True, blank=True`) used for soft-delete

#### 4.2 `Role`
Fields:
- `role`: unique role name
- `permission`: ArrayField of strings (permission codes)
- `is_admin`: boolean; bypasses normal permission checks

Method:
- `__str__` returns role name

#### 4.3 `Admin`
Fields:
- `name`, `email` (unique), `phone` (unique)
- `password` (stores hashed password)
- `status` boolean (active/inactive)
- `role` FK → `Role` with `on_delete=PROTECT`

Methods:
- `set_password(raw_password)` → uses `make_password`
- `verify_password(raw_password)` → uses `check_password`

Properties:
- `is_authenticated` returns True
- `is_anonymous` returns False

#### 4.4 `Category`
Fields:
- `name` unique
- `slug` unique
- `parent`: self-FK (supports hierarchy)
- `description`, `image`, `is_active`

#### 4.5 `Supplier`
Fields:
- `name`, `code` unique
- `contact_person`, `phone`
- `email`, `address`, `city`, `country`, `tax_number`
- `is_active`

#### 4.6 `Product`
Fields:
- `name`, `product_id` unique (nullable)
- `category` FK → Category
- `supplier` FK → Supplier (nullable, SET_NULL)
- `buying_price`, `quantity`, `unit` (choices)
- `reorder_level`
- `image`
- `opening_stock`, `stock_on_way`
- `is_active`

Property:
- `stock_status`
  - If `quantity == 0` → `out_of_stock`
  - If `quantity <= reorder_level` → `low_stock`
  - Else → `in_stock`

#### 4.7 `Employee`
Fields:
- `name`, `contact_number`, `email` unique
- `availability`: (`available` / `unavailable`)
- `delivered_orders` integer
- `image`

#### 4.8 `Order`
Fields:
- `product` FK → Product
- `quantity`
- `order_value`
- `status` choices:
  - confirmed, out_for_delivery, cancelled, catering
- `assigned_employee` FK → Employee nullable SET_NULL

#### 4.9 `AdminProfile`
Fields:
- `admin`: OneToOneField → Admin
- `user_id`
- `notifications_enabled`
- `location_enabled`

---

### File: `adminside/admin.py`
- Registers models in Django admin:
  - Role, Admin, Category, Supplier, Product, AdminProfile, Employee

---

### File: `adminside/authentication.py`
Defines JWT authentication class for DRF.

#### `AdminJWTAuthentication`
- Extends `rest_framework_simplejwt.authentication.JWTAuthentication`
- Overrides `get_user(validated_token)`:
  - Reads `admin_id` or `user_id` from JWT payload
  - Fetches `Admin` by `id`, ensuring:
    - `deleted_at__isnull=True`
    - `status=True`
  - Raises `AuthenticationFailed` if missing/invalid

Aliases:
- `AdminTokenAuthentication = AdminJWTAuthentication`

---

### File: `adminside/permissions.py`
Custom DRF permission classes.

#### `IsRoleAdmin`
- Allows access only if:
  - `request.user` exists
  - user is authenticated
  - and `request.user.role.is_admin` is True

#### `HasRolePermission`
- Role-based permission checking using `role.permission` ArrayField.
- Admin role (`role.is_admin == True`) bypasses checks.
- Otherwise:
  - Determines required permissions from `view.required_permissions` (if present)
  - Intersects required permissions with granted permissions from role.permission

Note:
- If `required_permissions` not configured or resolves to empty set, it allows access.

---

### File: `adminside/serializers.py`
DRF serializers for models and API payloads.

#### Role serializers
- `RoleSerializer`: `fields='__all__'`, read-only timestamps/deleted
- `RoleListSerializer`: lighter response fields for listing

#### Admin serializer
- `AdminUserSerializer`
  - adds write-only `password`
  - `create()` hashes password via `admin.set_password`
  - read-only: `id`, `created_at`, `updated_at`, `deleted_at`

#### Auth-related request serializers
- `AdminLoginSerializer`: email + password
- `AdminForgotPasswordSerializer`: email
- `AdminChangePasswordSerializer`: password, new_password, confirm_password
  - (Note: current view returns success without actually changing the password—see views section.)

#### Soft-delete serializer base
- `BaseSoftDeleteSerializer`: `fields='__all__'` + timestamps read-only

Entity serializers (all based on BaseSoftDeleteSerializer):
- `CategorySerializer`
- `SupplierSerializer`
- `ProductSerializer` (also exposes `stock_status` as read-only)
- `EmployeeSerializer`
- `OrderSerializer`
- `AdminProfileSerializer`

#### `DashboardSerializer`
- Defines metrics fields used by dashboard UI.
- `from_metrics()` computes:
  - `total_sales`: Sum of `Order.order_value` over non-deleted orders
  - `total_revenue`: Sum excluding cancelled
  - `active_orders`: count excluding cancelled
  - `cancel_orders`: count of status=cancelled
  - `categories`: count of non-deleted categories
  - `products`: count of non-deleted products
  - `low_stock`: count of products that are 0 quantity OR <= reorder_level
  - `available_employees`: count where availability='available' and non-deleted

---

### File: `adminside/views.py`
Core API logic.

#### 5.1 `SoftDeleteModelViewSet`
Common behavior for CRUD viewsets.
- `get_queryset()` filters out soft-deleted rows unless query param `include_deleted=true`
- `perform_destroy()` performs soft delete by setting `deleted_at=timezone.now()` and saving `deleted_at`/`updated_at`

#### 5.2 CRUD ViewSets
All use:
- `authentication_classes=[AdminJWTAuthentication]`
- `permission_classes=[IsAuthenticated]` or role-based permissions

ViewSets:
- `RoleView`
  - Uses `IsAuthenticated, IsRoleAdmin`
  - Uses `RoleListSerializer` for list action, else `RoleSerializer`

- `AdminUserViewSet`
  - `permission_classes=[IsAuthenticated, HasRolePermission]`
  - queryset uses `select_related('role')`

- `CategoryViewSet`
- `SupplierViewSet`
- `ProductViewSet` (select_related category + supplier)
- `EmployeeViewSet`
- `OrderViewSet` (select_related product + assigned_employee)
- `AdminProfileViewSet` (select_related admin)

#### 5.3 Dashboard metrics API
- `DashboardMetricsAPIView`
  - GET only
  - Uses `DashboardSerializer.from_metrics()` and returns computed metrics

Route: `/api/v1/admin/dashboard/`
(as configured in `adminside/urls.py`)

#### 5.4 Authentication APIs (JWT)
- `AdminLoginAPIView`
  - No DRF auth/permission required (public endpoint)
  - POST:
    1. Validates email/password
    2. Retrieves active non-deleted Admin record
    3. Verifies password hash
    4. Creates JWT refresh token and embeds custom claims:
       - `admin_id`, `role_id`, `is_admin`
    5. Returns:
       - `access` token
       - `refresh` token
       - `admin` details (AdminUserSerializer)

- `AdminTokenRefreshAPIView`
  - POST:
    - Reads refresh token from Authorization header (expects raw token or `Bearer <token>`)
    - Validates with `TokenRefreshSerializer`
    - Returns validated data (access token refresh flow)

- `AdminLogoutAPIView`
  - POST:
    - Requires JWT auth
    - Extracts refresh token from Authorization header
    - Calls `RefreshToken(token).blacklist()`
    - Returns success or error on invalid/expired

#### 5.5 Password reset / change APIs
- `AdminForgotPasswordAPIView`
  - POST:
    - Always responds with reset token if email exists; otherwise generic message
    - If admin found:
      - `uid` = urlsafe_base64_encode(pk)
      - `reset_token` = default_token_generator.make_token(admin)

- `AdminChangePasswordAPIView`
  - POST:
    - Validates serializer fields
    - CURRENTLY does not implement actual password update logic.
    - Always returns `{ "detail": "Password changed successfully." }`
  - (This is a placeholder/unfinished implementation.)

#### 5.6 UI Template Routing API
- `AdminTemplateView`
  - Requires JWT auth and role admin permissions
  - GET:
    - If `page == "login"` → renders `authentication/login.html`
    - Else → renders `dashboard/dashboard.html` with context `{"page": page}`

And exports:
- `AdminView = AdminUserViewSet`

---

### File: `adminside/urls.py`
Defines API routes and UI template routes.

Uses a DRF `DefaultRouter()` and registers viewsets:
- `manage-roles/`:
  - `role` → `RoleView`
  - `admins` → `AdminUserViewSet`
  - `categories` → `CategoryViewSet`
  - `suppliers` → `SupplierViewSet`
  - `products` → `ProductViewSet`
  - `employees` → `EmployeeViewSet`
  - `orders` → `OrderViewSet`
  - `profiles` → `AdminProfileViewSet`

Additional endpoints:
- `dashboard/` → `DashboardMetricsAPIView`
- `auth/login/` → `AdminLoginAPIView`
- `auth/refresh/` → `AdminTokenRefreshAPIView`
- `auth/logout/` → `AdminLogoutAPIView`
- `auth/forgot-password/` → `AdminForgotPasswordAPIView`
- `auth/change-password/` → `AdminChangePasswordAPIView`

Server-rendered UI templates:
- `login/` → `AdminTemplateView` with page=login
- `ui/dashboard/` → `AdminTemplateView` with page=dashboard
- `ui/<page>/` → generic routing to dashboard template with page
- `ui/` → defaults to dashboard

---

### File: `adminside/management/commands/create_super_admin.py`
Bootstrap command to create/update an admin super-user.

Behavior:
- Ensures a `Role` exists for the provided `--role` (default: `admin`)
  - Forces `is_admin=True` and `permission=['all']`
- Ensures an Admin exists for the provided `--email`
  - Creates with provided name/phone/password
  - If Admin exists, updates name/phone/status/role/password
- Prevents creating a second super admin under the same role with a different email (raises CommandError if another super admin exists)

---

### File: `adminside/tests.py`
- Contains API tests for serializer output differences.

Tests validate:
- List endpoints exclude timestamp fields: `created_at`, `updated_at`, `deleted_at`
- Detail endpoints include timestamp fields

> Note: These tests reference URL names like `roles-list`, `roles-detail`, etc.
- These names come from DRF router conventions.

---

## 5) Templates & Frontend UI

### File: `adminside/templates/layout/base.html`
- Base admin layout template.
- Includes:
  - `adminside/layout/sidebar.html`
  - `adminside/layout/navbar.html`
- Defines template blocks:
  - `title`
  - `css`
  - `content`
  - `js`

### File: `adminside/templates/layout/sidebar.html`
- Sidebar navigation markup.
- Currently anchor links are placeholders (`href="#"`).

### File: `adminside/templates/layout/navbar.html`
- Top bar markup.
- Contains a search input and notification/profile area.

### File: `adminside/templates/authentication/login.html`
Login page UI.
- Includes Bootstrap styling and `adminside/css/style.css`.
- Contains a form with fields:
  - email
  - password
- JavaScript:
  - On submit, calls `/api/v1/admin/auth/login/` using `fetch`
  - On success:
    - stores JWT tokens in `localStorage`:
      - `admin_access`
      - `admin_refresh`
    - redirects browser to `/api/v1/admin/ui/`

### File: `adminside/templates/dashboard/dashboard.html`
Dashboard metrics page.
- Displays metric counters:
  - sales (id `sales`)
  - revenue (id `revenue`)
  - orders (id `orders`)
  - cancelled (id `cancelled`)
- Contains a `<pre id="metrics">` element where JSON metrics are displayed
- Includes dashboard JS via `{% static 'adminside/js/dashboard.js' %}`

### Files: `adminside/templates/dashboard/employee.html`, `inventory.html`, `orders.html`, `reports.html`
- Extracted content in this session returned empty strings for some of these files.
- The router/UI currently renders only `dashboard/dashboard.html` with a `page` variable, so these may be unused placeholders or intended for later expansion.

---

## 6) Static Assets

### File: `adminside/static/css/style.css`
- Styling for admin layout.
- Defines styles for:
  - overall page background and font
  - sidebar and topbar
  - cards and responsive behavior

### File: `adminside/static/js/dashboard.js`
Client-side metrics loader.

Behavior:
- On document ready:
  - reads token from `localStorage.getItem('access')` (note: login stores `admin_access`; token key mismatch)
  - if token missing: writes `Login required` to `#metrics`
  - else calls `/api/v1/admin/dashboard/metrics/` with Authorization header:
    - `Bearer <token>`
  - Updates DOM:
    - `#sales`, `#revenue`, `#orders`, `#cancelled`
  - Writes JSON response to `#metrics`

> **Important**: In `adminside/urls.py`, the endpoint is `dashboard/` not `dashboard/metrics/`. Also the JS uses a different localStorage key. This mismatch will prevent metrics from loading until corrected.

---

## 7) Summary of End-to-End Flows

### Flow A — Admin login
1. User opens `/api/v1/admin/login/` → `AdminTemplateView(page='login')`
2. User submits credentials to `/api/v1/admin/auth/login/`
3. Server validates `Admin` and password
4. Server returns JWT access + refresh
5. Client stores tokens and redirects to `/api/v1/admin/ui/`

### Flow B — Dashboard metrics
1. User loads `/api/v1/admin/ui/` (dashboard template)
2. `dashboard.js` requests metrics endpoint
3. `DashboardMetricsAPIView` computes metrics via DB queries
4. UI updates cards and prints metrics JSON

### Flow C — CRUD with soft-delete
- Viewsets use `SoftDeleteModelViewSet`
- Delete marks `deleted_at` instead of removing rows
- List endpoints exclude `deleted_at != null` rows by default

---

## 8) Notable Issues / Gaps (documented for completeness)

1. **Password change endpoint is incomplete**
   - `AdminChangePasswordAPIView` validates but does not change the password in DB.

2. **Dashboard JS endpoint + token key mismatch**
   - JS calls `/api/v1/admin/dashboard/metrics/` but Django routes `dashboard/`
   - JS reads `localStorage['access']` but login stores `admin_access`

3. **Some dashboard sub-templates may be placeholders**
   - `AdminTemplateView` always renders `dashboard/dashboard.html` regardless of `page`.

---

## 9) File Index (quick reference)

- `manage.py`
- `BOandMIE/settings.py`
- `BOandMIE/urls.py`
- `BOandMIE/asgi.py`, `BOandMIE/wsgi.py`
- `adminside/apps.py`
- `adminside/models.py`
- `adminside/admin.py`
- `adminside/authentication.py`
- `adminside/permissions.py`
- `adminside/serializers.py`
- `adminside/views.py`
- `adminside/urls.py`
- `adminside/tests.py`
- `adminside/management/commands/create_super_admin.py`
- `adminside/templates/layout/base.html`
- `adminside/templates/layout/navbar.html`
- `adminside/templates/layout/sidebar.html`
- `adminside/templates/authentication/login.html`
- `adminside/templates/dashboard/dashboard.html`
- `adminside/static/css/style.css`
- `adminside/static/js/dashboard.js`


