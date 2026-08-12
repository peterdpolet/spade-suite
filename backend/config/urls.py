from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('djoser.urls')),
    path('api/auth/', include('djoser.urls.jwt')),
    path('api/', include('boards.urls')),
    path('api/', include('teams.urls')),
    path('api/', include('issues.urls')),
    path('api/', include('comments.urls')),
    path('api/', include('labels.urls')),
    path('api/', include('activities.urls')),
    path('api/', include('flows.urls')),
    path('api-auth/', include('rest_framework.urls')),
]