from django.contrib import admin
from django.urls import path
from . import views
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

schema_view = get_schema_view(
    openapi.Info(
        title="API Spellcast",
        default_version='v1',
        description="Documentación de la API para el proyecto Spellcast",
    ),
    public=True,
)

urlpatterns = [
    path('', views.home, name='home'),
    # Documentación:
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    path('test/', views.test, name='test'),
]
