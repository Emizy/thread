from django.conf import settings
from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static
from core.views import account_logout

urlpatterns = [
    path('admin/', admin.site.urls),
    path("api/", include("config.api_urls")),
    path(r'api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    path(r'accounts/logout/', account_logout),
    path('silk-profiler', include('silk.urls', namespace='silk'))
]
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
