from django.contrib import admin
from .models import Category, Product

# Đăng ký 2 bảng Category và Product vào trang Admin
admin.site.register(Category)
admin.site.register(Product)