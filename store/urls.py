from django.urls import path
from .views import (
    ProductListView, CreateOrderView, 
    AdminDashboardView, RestockProductView, 
    RegisterView, VerifyOTPView,
    AdminProductListCreateView, AdminProductDetailView,
    ProductDetailView, CreateReviewView, UserChatView, AdminChatView, AdminChatCustomerListView,
    SiteContentDetailView, AdminDeleteReviewView, 
    AdminDeleteMediaView, AdminAnalyticsView    
)

urlpatterns = [
    path('products/', ProductListView.as_view(), name='product-list'),
    path('orders/', CreateOrderView.as_view(), name='create-order'),
    path('register/', RegisterView.as_view(), name='register'),
    path('verify-otp/', VerifyOTPView.as_view(), name='verify-otp'),
    
    # API Admin
    path('admin/dashboard/', AdminDashboardView.as_view(), name='admin-dashboard'),
    path('admin/products/<int:pk>/restock/', RestockProductView.as_view(), name='admin-restock'),
    
    # API Admin - Quản lý Thực đơn (CRUD)
    path('admin/products/', AdminProductListCreateView.as_view(), name='admin-product-list-create'),
    path('admin/products/<int:pk>/', AdminProductDetailView.as_view(), name='admin-product-detail'),

    # API Trang Chi tiết Sản phẩm & Đánh giá
    path('products/<int:pk>/', ProductDetailView.as_view(), name='product-detail'),
    path('products/<int:pk>/reviews/', CreateReviewView.as_view(), name='create-review'),
        
    # API Chat trực tiếp với Người bán
    path('chat/', UserChatView.as_view(), name='user-chat'),
    # API Chat phía Admin:
    path('admin/chat/customers/', AdminChatCustomerListView.as_view(), name='admin-chat-customers'),
    path('admin/chat/', AdminChatView.as_view(), name='admin-chat'),

    # API Nội dung trang chủ
    path('site-content/<str:key>/', SiteContentDetailView.as_view(), name='site-content-detail'),
    
    # API Xóa Review & Media dành cho Admin
    path('admin/reviews/<int:pk>/', AdminDeleteReviewView.as_view(), name='admin-delete-review'),
    path('admin/media/<int:pk>/', AdminDeleteMediaView.as_view(), name='admin-delete-media'),
    
    # API Phân tích Doanh thu nâng cao
    path('admin/analytics/', AdminAnalyticsView.as_view(), name='admin-analytics'),
]