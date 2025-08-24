from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),

    # API routes
    path("api/", include("api.urls")),

    # DRF browsable API login/logout
    path("api-auth/", include("rest_framework.urls")),

    # JWT auth routes
    path('api/auth/', include('api.urls')),  

]
