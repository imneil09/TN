from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Admin Panel
    path('admin/', admin.site.urls),
    
    # Include the News App URLs
    path('', include('news.urls')), 
]

# Serve media files (uploaded images) in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    # Optional: Serve static files if not automatically handled
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])