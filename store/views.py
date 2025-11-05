from django.shortcuts import render, get_object_or_404, redirect
from django.views import View
from django.contrib.auth import get_user_model, authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils import timezone
from django.contrib import messages
from django.db.models import Q, Avg
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from decimal import Decimal

from .models import (
    Product, CartItem, Order, OrderItem,
    ContactMessage, HeroBanner, Sale, Category, Review
)
from .forms import ContactForm, RegisterForm, ReviewForm

User = get_user_model()

# --- вспомогательная функция ---
def _get_session_key(request):
    """Возвращает session_key, создаёт если нет."""
    if not request.session.session_key:
        request.session.create()
    return request.session.session_key


# --- Главная страница ---
def index(request):
    products = Product.objects.all()
    banners = HeroBanner.objects.filter(active=True).order_by('order')
    categories = Category.objects.all()
    return render(request, 'index.html', {
        'products': products,
        'banners': banners,
        'categories': categories,
    })
