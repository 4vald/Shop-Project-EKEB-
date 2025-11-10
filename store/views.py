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
    ContactMessage, HeroBanner, Sale, Category, Review, UserProfile
)
from .forms import ContactForm, RegisterForm, ReviewForm, UserProfileForm


User = get_user_model()


# --- вспомогательная функция для сессии ---
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


# --- Детали товара ---
def product_detail(request, product_id):
    product = get_object_or_404(Product, pk=product_id)
    avg_rating = product.reviews.aggregate(Avg('rating'))['rating__avg'] or 0
    form = ReviewForm()
    return render(request, 'product_detail.html', {
        'product': product,
        'form': form,
        'avg_rating': avg_rating,
    })


# --- Добавление товара в корзину ---
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    quantity = int(request.POST.get('quantity', 1)) if request.method == "POST" else 1

    if request.user.is_authenticated:
        filter_args = {'user': request.user, 'product': product}
    else:
        session_key = _get_session_key(request)
        filter_args = {'session_key': session_key, 'product': product}

    cart_item, created = CartItem.objects.get_or_create(defaults={'quantity': quantity}, **filter_args)
    if not created:
        cart_item.quantity += quantity
        cart_item.save()

    return redirect('store:cart')


# --- Просмотр корзины ---
class CartView(View):
    def get(self, request):
        if request.user.is_authenticated:
            items = CartItem.objects.filter(user=request.user)
        else:
            session_key = _get_session_key(request)
            items = CartItem.objects.filter(session_key=session_key)

        total = sum(
            (getattr(it.product, 'discounted_price', it.product.price)) * it.quantity
            for it in items
        )
        return render(request, 'cart.html', {'items': items, 'total': total})


# --- Обновление или удаление позиции в корзине ---
class UpdateCartItemView(View):
    def post(self, request, pk):
        item = get_object_or_404(CartItem, pk=pk)
        action = request.POST.get('action')

        if action == 'remove' or request.POST.get('quantity') == '0':
            item.delete()
        else:
            try:
                qty = int(request.POST.get('quantity', 1))
            except ValueError:
                qty = 1
            item.quantity = max(qty, 1)
            item.save()

        return redirect('store:cart')


# --- Оформление заказа ---
class CheckoutView(LoginRequiredMixin, View):
    login_url = '/login/'

    def post(self, request):
        user = request.user
        items = CartItem.objects.filter(user=user)
        if not items.exists():
            messages.error(request, "Ваша корзина пуста.")
            return redirect('store:cart')

        full_name = request.POST.get('full_name', '').strip()
        address = request.POST.get('address', '').strip()
        phone = request.POST.get('phone', '').strip()

        if not all([full_name, address, phone]):
            messages.error(request, "Заполните все поля.")
            return redirect('store:cart')

        order = Order.objects.create(
            user=user,
            full_name=full_name,
            address=address,
            phone=phone,
            created=timezone.now(),
            status='processing',
            total=Decimal('0.00')
        )

        total = Decimal('0.00')
        for it in items:
            product = it.product
            sale = getattr(product, 'active_sale', None)

            if sale and sale.discount_percent > 0:
                discount_percent = Decimal(sale.discount_percent)
                price = product.price * (Decimal('1.0') - discount_percent / Decimal('100'))
            else:
                price = product.price
                discount_percent = Decimal('0')

            OrderItem.objects.create(
                order=order,
                product=product,
                price=price,
                quantity=it.quantity,
                original_price=product.price,
                discount_percent=discount_percent
            )
            total += price * it.quantity

        order.total = total
        order.save()
        items.delete()

        request.session['last_order_id'] = order.id
        messages.success(request, "Заказ оформлен!")
        return redirect('store:payment_success')


# --- Страница успеха оплаты ---
def payment_success(request):
    last_order_id = request.session.get('last_order_id')
    order = None

    if last_order_id:
        order = Order.objects.filter(pk=last_order_id).first()
        if order and order.status == 'processing':
            order.status = 'paid'
            order.save()

    return render(request, 'payment_success.html', {'order': order})


# --- История заказов ---
def orders(request):
    if request.user.is_authenticated:
        qs = Order.objects.filter(user=request.user).order_by('-created')
    else:
        last_order_id = request.session.get('last_order_id')
        qs = Order.objects.filter(pk=last_order_id) if last_order_id else Order.objects.none()
    return render(request, 'orders.html', {'orders': qs})


# --- Статические страницы ---
def about(request):
    return render(request, 'about.html')


def contact(request):
    return render(request, 'contact.html')


def contact_view(request):
    if request.method == "POST":
        ContactMessage.objects.create(
            name=request.POST.get("name"),
            email=request.POST.get("email"),
            subject=request.POST.get("subject"),
            message=request.POST.get("message")
        )
        messages.success(request, "Ваше сообщение успешно отправлено!")
        return redirect("store:contact")
    return render(request, "contact.html")


# --- Авторизация / регистрация ---
def login_view(request):
    if request.method == "POST":
        user = authenticate(request,
                            username=request.POST.get("username"),
                            password=request.POST.get("password"))
        if user:
            login(request, user)
            messages.success(request, f"Добро пожаловать, {user.username}!")
            return redirect("store:index")
        messages.error(request, "Неверное имя пользователя или пароль.")
    return render(request, "login.html")


def logout_view(request):
    logout(request)
    messages.info(request, "Вы вышли из системы.")
    return redirect("store:index")


def register_view(request):
    form = RegisterForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Аккаунт создан! Теперь войдите в систему.")
        return redirect("store:login")
    elif request.method == "POST":
        messages.error(request, "Ошибка при регистрации. Проверьте данные.")
    return render(request, "register.html", {"form": form})


# --- Акции ---
def sale_list(request):
    return render(request, 'sale_list.html', {'sales': Sale.objects.all()})


def sale_detail(request, sale_id):
    sale = get_object_or_404(Sale, id=sale_id)
    return render(request, 'sale_detail.html', {
        'sale': sale,
        'products': sale.products.all()
    })


# --- Поиск товаров ---
def search_products(request):
    query = request.GET.get('q', '').strip()
    category_id = request.GET.get('category', '')
    min_price = request.GET.get('min_price', '')
    max_price = request.GET.get('max_price', '')
    has_discount = request.GET.get('has_discount', '')

    products = Product.objects.all()

    if query:
        products = products.filter(Q(title__icontains=query) | Q(description__icontains=query))
    if category_id.isdigit():
        products = products.filter(category_id=int(category_id))
    try:
        if min_price:
            products = products.filter(price__gte=float(min_price))
        if max_price:
            products = products.filter(price__lte=float(max_price))
    except ValueError:
        pass
    if has_discount == '1':
        products = products.filter(sales__discount_percent__gt=0).distinct()

    return render(request, 'search_results.html', {
        'products': products,
        'query': query,
        'categories': Category.objects.all(),
        'selected_category': int(category_id) if category_id.isdigit() else None,
        'min_price': min_price,
        'max_price': max_price,
        'has_discount': has_discount
    })


# --- Отзывы ---
@login_required
def add_review(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    form = ReviewForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        review = form.save(commit=False)
        review.user = request.user
        review.product = product
        review.save()
        messages.success(request, "Отзыв добавлен!")
    return redirect('store:product_detail', product_id=product.id)


# --- AJAX обновление количества товара в корзине ---
@csrf_exempt
def update_cart_quantity(request):
    """Обновление количества товара в корзине (AJAX, с учетом скидок)."""
    if request.method != "POST":
        return JsonResponse({"success": False, "error": "Метод не поддерживается"}, status=405)

    try:
        item_id = int(request.POST.get("item_id", 0))
        quantity = int(request.POST.get("quantity", 1))
        if quantity < 1:
            return JsonResponse({"success": False, "error": "Количество должно быть ≥ 1"}, status=400)

        item = CartItem.objects.select_related("product").get(pk=item_id)
        product = item.product
        item.quantity = quantity
        item.save()

        original_price = float(product.price)
        discounted_price = float(product.discounted_price)
        has_discount = discounted_price < original_price
        item_total = discounted_price * quantity

        if request.user.is_authenticated:
            items = CartItem.objects.filter(user=request.user).select_related("product")
        else:
            session_key = _get_session_key(request)
            items = CartItem.objects.filter(session_key=session_key).select_related("product")

        cart_total = sum(float(it.product.discounted_price) * it.quantity for it in items)

        def fmt(v):
            return f"₸{v:,.0f}".replace(",", " ")

        return JsonResponse({
            "success": True,
            "has_discount": has_discount,
            "original_total": fmt(original_price * quantity) if has_discount else None,
            "discounted_total": fmt(item_total),
            "cart_total": fmt(cart_total),
        })

    except (ValueError, TypeError):
        return JsonResponse({"success": False, "error": "Некорректные данные"}, status=400)
    except CartItem.DoesNotExist:
        return JsonResponse({"success": False, "error": "Товар не найден"}, status=404)

@login_required
def profile_view(request):
    profile, created = UserProfile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=profile)  # <--- добавлено request.FILES
        if form.is_valid():
            form.save()
            messages.success(request, 'Профиль успешно обновлён.')
            return redirect('store:profile')
    else:
        form = UserProfileForm(instance=profile)

    return render(request, 'profile.html', {'form': form})
