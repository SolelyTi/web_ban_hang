from rest_framework import serializers
from .models import Category, Product, Order, OrderItem, ProductMedia, ProductReview, ChatMessage, SiteContent
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth.models import User
from django.db.models import Avg

# Thông dịch viên cho Category
class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name']

# Thông dịch viên cho Product
from rest_framework import serializers
from .models import Product, Category

class ProductSerializer(serializers.ModelSerializer):
    category_name = serializers.ReadOnlyField(source='category.name')

    class Meta:
        model = Product
        fields = ['id', 'category', 'category_name', 'name', 'description', 'price', 'stock', 'image', 'created_at']

# Thông dịch viên cho món hàng nằm trong đơn
class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ['product', 'quantity']

# Thông dịch viên cho toàn bộ Đơn hàng
class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True) # Danh sách các món đặt mua

    class Meta:
        model = Order
        fields = ['id', 'created_at', 'total_price', 'items']

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        # Thêm thông tin User vào Response trả về cho Frontend
        data['username'] = self.user.username
        data['is_staff'] = self.user.is_staff
        return data

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password']

    def create(self, validated_data):
        email = validated_data.get('email')
        if not email:
            raise serializers.ValidationError({"email": "Email không được để trống!"})
            
        user = User.objects.create_user(
            username=validated_data['username'],
            email=email,
            password=validated_data['password'],
            is_active=False # CHẶN ĐĂNG NHẬP CHO ĐẾN KHI XÁC THỰC EMAIL
        )
        return user

# Serializer Ảnh/Video phụ
class ProductMediaSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductMedia
        fields = ['id', 'file', 'is_video']

# Serializer Đánh giá
class ProductReviewSerializer(serializers.ModelSerializer):
    username = serializers.ReadOnlyField(source='user.username')

    class Meta:
        model = ProductReview
        fields = ['id', 'username', 'rating', 'comment', 'created_at']

# Serializer Chi tiết Sản phẩm (Bao gồm Ảnh, Đánh giá, Điểm trung bình)
class ProductDetailSerializer(serializers.ModelSerializer):
    category_name = serializers.ReadOnlyField(source='category.name')
    media_files = ProductMediaSerializer(many=True, read_only=True)
    reviews = ProductReviewSerializer(many=True, read_only=True)
    average_rating = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            'id', 'category', 'category_name', 'name', 'description', 
            'price', 'stock', 'image', 'media_files', 'reviews', 'average_rating'
        ]

    def get_average_rating(self, obj):
        avg = obj.reviews.aggregate(Avg('rating'))['rating__avg']
        return round(avg, 1) if avg else 0.0

# Serializer Chat
class ChatMessageSerializer(serializers.ModelSerializer):
    sender_username = serializers.ReadOnlyField(source='sender.username')

    class Meta:
        model = ChatMessage
        fields = ['id', 'sender', 'sender_username', 'receiver', 'message', 'created_at']
        read_only_fields = ['sender', 'receiver']

# Serializer Nội dung Trang chủ
class SiteContentSerializer(serializers.ModelSerializer):
    class Meta:
        model = SiteContent
        fields = ['key', 'value']




