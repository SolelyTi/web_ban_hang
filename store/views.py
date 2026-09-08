import random
from django.db import transaction
from django.db.models import Sum, Q, Avg, Count
from django.core.mail import send_mail
from django.contrib.auth.models import User
from django.shortcuts import render
from django.db.models.functions import TruncDate, Coalesce

from rest_framework import status, views, generics, permissions, serializers
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from rest_framework_simplejwt.views import TokenObtainPairView

from .models import Category, Product, Order, OrderItem, ProductMedia, ProductReview, ChatMessage, SiteContent
from .serializers import (
    ProductSerializer, OrderSerializer, CustomTokenObtainPairSerializer,
    RegisterSerializer, ProductMediaSerializer, ProductReviewSerializer,
    ProductDetailSerializer, ChatMessageSerializer, SiteContentSerializer
)

OTP_STORAGE = {}

# Hàm xử lý: Trả về danh sách tất cả các sản phẩm (GET)
class ProductListView(generics.ListAPIView):
    queryset = Product.objects.all()  # Lấy tất cả sản phẩm trong CSDL
    serializer_class = ProductSerializer  # Dùng thông dịch viên ProductSerializer để biến thành JSON

class CreateOrderView(views.APIView):
    permission_classes = [IsAuthenticated] # BẮT BUỘC ĐÃ ĐĂNG NHẬP MỚI ĐƯỢC VÀO

    def post(self, request):
        # Lấy thông tin user từ Token gửi lên
        current_user = request.user 
        
        items_data = request.data.get('items', [])
        if not items_data:
            return Response({"error": "Đơn hàng phải có ít nhất 1 sản phẩm!"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            with transaction.atomic():
                total_price = 0
                # Gán người tạo đơn là user đang đăng nhập
                order = Order.objects.create(total_price=0, user=current_user) 

                for item in items_data:
                    product_id = item.get('product')
                    quantity = item.get('quantity', 1)

                    product = Product.objects.select_for_update().get(id=product_id)

                    if product.stock < quantity:
                        raise Exception(f"Sản phẩm '{product.name}' không đủ số lượng trong kho (Còn: {product.stock})")

                    product.stock -= quantity
                    product.save()

                    total_price += product.price * quantity
                    OrderItem.objects.create(order=order, product=product, quantity=quantity)

                order.total_price = total_price
                order.save()

                return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)

        except Product.DoesNotExist:
            return Response({"error": "Sản phẩm không tồn tại!"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

class AdminDashboardView(views.APIView):
    permission_classes = [IsAdminUser] # BẮT BUỘC LÀ ADMIN/STAFF MỚI ĐƯỢC GỌI

    def get(self, request):
        total_products = Product.objects.count()
        low_stock_products = Product.objects.filter(stock__lt=5).values('id', 'name', 'stock') # Món sắp hết (< 5)
        total_revenue = Order.objects.aggregate(Sum('total_price'))['total_price__sum'] or 0
        total_orders = Order.objects.count()

        return Response({
            "total_products": total_products,
            "total_orders": total_orders,
            "total_revenue": total_revenue,
            "low_stock_products": list(low_stock_products)
        })

class RestockProductView(views.APIView):
    permission_classes = [IsAdminUser]

    def patch(self, request, pk):
        try:
            product = Product.objects.get(pk=pk)
            amount = request.data.get('amount', 0)
            if amount <= 0:
                return Response({"error": "Số lượng nhập phải lớn hơn 0"}, status=status.HTTP_400_BAD_REQUEST)
            
            product.stock += int(amount)
            product.save()
            return Response({"message": f"Đã nhập thêm {amount} ly cho {product.name}", "new_stock": product.stock})
        except Product.DoesNotExist:
            return Response({"error": "Sản phẩm không tồn tại"}, status=status.HTTP_404_NOT_FOUND)

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = [AllowAny]
    serializer_class = RegisterSerializer

    def perform_create(self, serializer):
        user = serializer.save()
        
        # 1. Tạo mã OTP 6 chữ số
        otp = str(random.randint(100000, 999999))
        OTP_STORAGE[user.email] = otp

        # 2. Gửi Email thực tế
        subject = 'Mã xác thực tài khoản - Cửa Hàng Trà Sữa'
        message = f'Chào {user.username},\n\nMã OTP xác thực tài khoản của bạn là: {otp}\nMã có hiệu lực trong vài phút.'
        send_mail(subject, message, None, [user.email])

class VerifyOTPView(views.APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get('email')
        otp_input = request.data.get('otp')

        if not email or not otp_input:
            return Response({"error": "Vui lòng cung cấp Email và mã OTP!"}, status=status.HTTP_400_BAD_REQUEST)

        # Kiểm tra mã OTP
        if OTP_STORAGE.get(email) == str(otp_input):
            try:
                user = User.objects.get(email=email)
                user.is_active = True # KÍCH HOẠT TÀI KHOẢN
                user.save()
                del OTP_STORAGE[email] # Xóa OTP đã dùng
                return Response({"message": "Xác thực Email thành công! Bạn hiện có thể đăng nhập."}, status=status.HTTP_200_OK)
            except User.DoesNotExist:
                return Response({"error": "Tài khoản không tồn tại!"}, status=status.HTTP_404_NOT_FOUND)
        else:
            return Response({"error": "Mã OTP không chính xác!"}, status=status.HTTP_400_BAD_REQUEST)

# API Thêm món mới & Xem danh sách quản lý
class AdminProductListCreateView(generics.ListCreateAPIView):
    queryset = Product.objects.all().order_by('-id')
    serializer_class = ProductSerializer
    permission_classes = [IsAdminUser]

# API Sửa & Xóa món ăn
class AdminProductDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [IsAdminUser]

# 1. API Xem Chi tiết Sản phẩm (Ai cũng xem được)
class ProductDetailView(generics.RetrieveAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductDetailSerializer
    permission_classes = [permissions.AllowAny]

# 2. API Gửi Đánh giá Sản phẩm (Yêu cầu Đăng nhập)
class CreateReviewView(generics.CreateAPIView):
    serializer_class = ProductReviewSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        product_id = self.kwargs['pk']
        product = Product.objects.get(pk=product_id)
        serializer.save(user=self.request.user, product=product)

# 3. API Lấy danh sách & Gửi tin nhắn Chat với Admin
class UserChatView(generics.ListCreateAPIView):
    serializer_class = ChatMessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        # Lấy tất cả tin nhắn giữa User này và bất kỳ Admin nào
        return ChatMessage.objects.filter(Q(sender=user) | Q(receiver=user)).order_by('created_at')

    def perform_create(self, serializer):
        # Tự động gán người nhận (receiver) là Admin đầu tiên trong hệ thống
        admin_user = User.objects.filter(is_staff=True).first()
        if not admin_user:
            # Nếu chưa có admin thì mặc định gán cho superuser
            admin_user = User.objects.filter(is_superuser=True).first()
            
        serializer.save(sender=self.request.user, receiver=admin_user)

# 2. API Dành riêng cho Admin (Xem danh sách khách hàng & Nhắn tin lại cho từng Khách)
class AdminChatView(generics.ListCreateAPIView):
    serializer_class = ChatMessageSerializer
    permission_classes = [permissions.IsAdminUser] # Bắt buộc phải là Admin/Staff

    def get_queryset(self):
        # Lấy ID của khách hàng từ query parameter trên URL (?user_id=X)
        customer_id = self.request.query_params.get('user_id')
        if customer_id:
            return ChatMessage.objects.filter(
                Q(sender_id=customer_id) | Q(receiver_id=customer_id)
            ).order_by('created_at')
        return ChatMessage.objects.none()

    def perform_create(self, serializer):
        customer_id = self.request.data.get('receiver_id')
        if not customer_id:
            raise serializers.ValidationError({"receiver_id": "Cần cung cấp ID khách hàng để trả lời!"})
        
        customer = User.objects.get(pk=customer_id)
        serializer.save(sender=self.request.user, receiver=customer)

# 3. API Lấy danh sách các Khách Hàng đã từng nhắn tin cho Admin (Để Admin chọn trò chuyện)
class AdminChatCustomerListView(generics.GenericAPIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        # Tìm tất cả User (không phải staff) đã từng gửi tin nhắn hoặc nhận tin nhắn từ Admin
        chat_user_ids = ChatMessage.objects.values_list('sender', flat=True).distinct()
        customers = User.objects.filter(id__in=chat_user_ids, is_staff=False).values('id', 'username', 'email')
        return Response(list(customers))

# 2. API Xem & Sửa nội dung trang chủ dành cho Admin
class SiteContentDetailView(generics.RetrieveUpdateAPIView):
    queryset = SiteContent.objects.all()
    serializer_class = SiteContentSerializer
    lookup_field = 'key'

    def get_object(self):
        key = self.kwargs.get('key')
        obj, _ = SiteContent.objects.get_or_create(key=key, defaults={'value': ''})
        return obj

    def get_permissions(self):
        if self.request.method in ['PUT', 'PATCH']:
            return [permissions.IsAdminUser()]
        return [permissions.AllowAny()]

# 4. API Admin Xóa Bình luận/Đánh giá
class AdminDeleteReviewView(generics.DestroyAPIView):
    queryset = ProductReview.objects.all()
    permission_classes = [permissions.IsAdminUser]

# 5. API Admin Xóa Ảnh/Video phụ của sản phẩm
class AdminDeleteMediaView(generics.DestroyAPIView):
    queryset = ProductMedia.objects.all()
    permission_classes = [permissions.IsAdminUser]

# 6. API Phân tích Doanh thu & Đơn hàng Chi tiết (Analytics Dashboard)
class AdminAnalyticsView(views.APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        # Thống kê doanh thu & đơn hàng theo từng ngày
        daily_stats = Order.objects.annotate(date=TruncDate('created_at')) \
            .values('date') \
            .annotate(total_revenue=Sum('total_price'), total_orders=Count('id')) \
            .order_by('-date')[:7] # 7 ngày gần nhất

        # Top 5 sản phẩm bán chạy nhất
        top_products = Product.objects.annotate(sold_count=Coalesce(Sum('orderitem__quantity'), 0)) \
            .filter(sold_count__gt=0) \
            .values('id', 'name', 'sold_count') \
            .order_by('-sold_count')[:5]

        return Response({
            "daily_stats": list(daily_stats),
            "top_products": list(top_products)
        })
