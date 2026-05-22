import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("adminside", "0006_product"),
    ]

    operations = [
        migrations.CreateModel(
            name="AdminProfile",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("deleted_at", models.DateTimeField(blank=True, null=True)),
                ("user_id", models.CharField(max_length=80)),
                ("notifications_enabled", models.BooleanField(default=True)),
                ("location_enabled", models.BooleanField(default=False)),
            ],
            options={
                "abstract": False,
            },
        ),
        migrations.CreateModel(
            name="Employee",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("deleted_at", models.DateTimeField(blank=True, null=True)),
                ("name", models.CharField(max_length=120)),
                ("contact_number", models.CharField(max_length=20)),
                ("email", models.EmailField(max_length=254, unique=True)),
                (
                    "availability",
                    models.CharField(
                        choices=[
                            ("available", "Available"),
                            ("unavailable", "Unavailable"),
                        ],
                        default="available",
                        max_length=20,
                    ),
                ),
                ("delivered_orders", models.PositiveIntegerField(default=0)),
                (
                    "image",
                    models.ImageField(blank=True, null=True, upload_to="employees/"),
                ),
            ],
            options={
                "abstract": False,
            },
        ),
        migrations.CreateModel(
            name="Order",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("deleted_at", models.DateTimeField(blank=True, null=True)),
                ("quantity", models.PositiveIntegerField(default=1)),
                ("order_value", models.DecimalField(decimal_places=2, max_digits=12)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("confirmed", "Confirmed"),
                            ("out_for_delivery", "Out for delivery"),
                            ("cancelled", "Cancelled"),
                            ("catering", "Catering"),
                        ],
                        default="confirmed",
                        max_length=30,
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
        ),
        migrations.AddField(
            model_name="category",
            name="deleted_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="product",
            name="product_id",
            field=models.CharField(blank=True, max_length=50, null=True, unique=True),
        ),
        migrations.AlterField(
            model_name="category",
            name="image",
            field=models.ImageField(blank=True, null=True, upload_to="categories/"),
        ),
        migrations.AlterField(
            model_name="product",
            name="image",
            field=models.ImageField(blank=True, null=True, upload_to="products/"),
        ),
        migrations.AlterField(
            model_name="supplier",
            name="address",
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="supplier",
            name="city",
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AlterField(
            model_name="supplier",
            name="country",
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AlterField(
            model_name="supplier",
            name="email",
            field=models.EmailField(blank=True, max_length=254, null=True),
        ),
        migrations.AlterField(
            model_name="supplier",
            name="tax_number",
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AddIndex(
            model_name="product",
            index=models.Index(
                fields=["product_id"], name="adminside_p_product_c3e387_idx"
            ),
        ),
        migrations.AddField(
            model_name="adminprofile",
            name="admin",
            field=models.OneToOneField(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="profile",
                to="adminside.admin",
            ),
        ),
        migrations.AddField(
            model_name="order",
            name="assigned_employee",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="orders",
                to="adminside.employee",
            ),
        ),
        migrations.AddField(
            model_name="order",
            name="product",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="orders",
                to="adminside.product",
            ),
        ),
    ]