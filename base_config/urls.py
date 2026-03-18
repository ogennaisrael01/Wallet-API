from django.contrib import admin
from django.urls import path, include
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
 
# Swagger/OpenAPI schema
schema_view = get_schema_view(
    openapi.Info(
        title="Django Wallet-API",
        default_version="v1",
        description="Wallet-APP",
        contact=openapi.Contact(email="ogennaisrael@gmail.com"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)
 
urlpatterns = [
    # Admin interface
    path("admin/", admin.site.urls),

    # API endpoints
    path("api/", include("api.users.urls")),
    path("api/", include("api.wallet.urls")),
    
    # API Documentation
    path(
        "api/schema/swagger-ui/",
        schema_view.with_ui("swagger", cache_timeout=0),
        name="schema-swagger-ui",
    ),
    path(
        "api/schema/redoc/",
        schema_view.with_ui("redoc", cache_timeout=0),
        name="schema-redoc",
    ),
    path(
        "api/schema/",
        schema_view.without_ui(cache_timeout=0),
        name="schema-json",
    ),
]