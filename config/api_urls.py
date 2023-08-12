from django.conf.urls.static import static
from django.urls import path, re_path, include
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework.authentication import SessionAuthentication
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework import permissions

from core.routes import router as core_router
from config.settings import MEDIA_URL, MEDIA_ROOT
from django.conf import settings

schema_view = get_schema_view(
    openapi.Info(
        title="BLOG API",
        default_version='v1',
        description="BLOG API ENDPOINT DOCUMENTATION.",
        terms_of_service="https://blog.com/privacy_policy",
        contact=openapi.Contact(email="support@station.com"),
        license=openapi.License(name="OpenAPI License"),
    ),
    public=True,
    url=f'{settings.BASE_URL}/api',
    authentication_classes=(SessionAuthentication, JWTAuthentication,),
    permission_classes=(permissions.AllowAny,),
)
urlpatterns = [
    path('v1/', include(core_router.urls)),
    path(r'', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    re_path(r'^swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=1), name='schema-json'),
    path('apidoc/', schema_view.with_ui('redoc', cache_timeout=1), name='schema-redoc'),
]
urlpatterns += static(MEDIA_URL, document_root=MEDIA_ROOT)
