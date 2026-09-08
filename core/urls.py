from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView
from rest_framework_simplejwt.views import TokenRefreshView
from store.views import CustomTokenObtainPairView

from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', TemplateView.as_view(template_name='index.html'), name='home'),
    path('admin-dashboard/', TemplateView.as_view(template_name='admin.html'), name='admin_dashboard'),
    path('admin.html', TemplateView.as_view(template_name='admin.html'), name='admin_html'),
    path('product-detail.html', TemplateView.as_view(template_name='product-detail.html'), name='product_detail_html'),
    path('product-detail/', TemplateView.as_view(template_name='product-detail.html'), name='product_detail_page'),
    path('api/', include('store.urls')),
    
    path('api/token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)