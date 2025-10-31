from django.shortcuts import render, get_object_or_404, redirect
from django.views import View
from .models import Product, CartItem, Order, OrderItem,  ContactMessage, HeroBanner, Sale, Product
from django.contrib.auth import get_user_model, authenticate, login, logout
from django.utils import timezone
from .forms import ContactForm, RegisterForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin


User = get_user_model()

# --- вспомогательная функция для сессии ---
def _get_session_key(request):
    if not request.session.session_key:
        request.session.create()
    return request.session.session_key

# Главная — показывает реальные товары
from django.shortcuts import render
from .models import Product, HeroBanner


def index(request):
    products = Product.objects.all()
    banners = HeroBanner.objects.filter(active=True).order_by('order')
    return render(request, 'index.html', {'products': products, 'banners': banners})


def product_detail(request, product_id):
    product = get_object_or_404(Product, pk=product_id)
    return render(request, 'product_detail.html', {'product': product})

# Добавление товара в корзину (POST)
class AddToCartView(View):
    def post(self, request, pk):
        product = get_object_or_404(Product, pk=pk)
        try:
            quantity = int(request.POST.get('quantity', 1))
        except ValueError:
            quantity = 1
        if request.user.is_authenticated:
            item, created = CartItem.objects.get_or_create(user=request.user, product=product, defaults={'quantity': quantity})
            if not created:
                item.quantity += quantity
                item.save()
        else:
            session_key = _get_session_key(request)
            item, created = CartItem.objects.get_or_create(session_key=session_key, product=product, defaults={'quantity': quantity})
            if not created:
                item.quantity += quantity
                item.save()
        return redirect('store:cart')

# Просмотр корзины
class CartView(View):
    def get(self, request):
        if request.user.is_authenticated:
            items = CartItem.objects.filter(user=request.user)
        else:
            session_key = request.session.session_key
            items = CartItem.objects.filter(session_key=session_key)
        total = sum([it.subtotal() for it in items])
        return render(request, 'cart.html', {'items': items, 'total': total})

# Добавление товара в корзину
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    if request.user.is_authenticated:
        cart_item, created = CartItem.objects.get_or_create(
            user=request.user,
            product=product,
            defaults={'quantity': 1}
        )
        if not created:
            cart_item.quantity += 1
            cart_item.save()
    else:
        session_key = request.session.session_key
        if not session_key:
            request.session.create()
            session_key = request.session.session_key

        cart_item, created = CartItem.objects.get_or_create(
            session_key=session_key,
            product=product,
            defaults={'quantity': 1}
        )
        if not created:
            cart_item.quantity += 1
            cart_item.save()

    return redirect('store:cart') 


# Обновление/удаление позиции в корзине
class UpdateCartItemView(View):
    def post(self, request, pk):
        action = request.POST.get('action')
        item = get_object_or_404(CartItem, pk=pk)
        if action == 'remove':
            item.delete()
        else:
            try:
                qty = int(request.POST.get('quantity', 1))
            except ValueError:
                qty = 1
            if qty <= 0:
                item.delete()
            else:
                item.quantity = qty
                item.save()
        return redirect('store:cart')

# Checkout: создаёт заказ (status='processing'), создаёт OrderItems, очищает корзину,
# сохраняет last_order_id в сессии и редиректит на success page.
class CheckoutView(LoginRequiredMixin, View):
    login_url = '/login/'

    def post(self, request, *args, **kwargs):
        user = request.user
        items = CartItem.objects.filter(user=user)

        # Проверка: корзина пуста
        if not items.exists():
            messages.error(request, "Ваша корзина пуста. Добавьте товары перед оформлением заказа.")
            return redirect('store:cart')

        # Проверка обязательных полей
        full_name = request.POST.get('full_name', '').strip()
        address = request.POST.get('address', '').strip()
        phone = request.POST.get('phone', '').strip()

        if not all([full_name, address, phone]):
            messages.error(request, "Пожалуйста, заполните все поля формы.")
            return redirect('store:cart')

        # Создание заказа
        order = Order.objects.create(
            user=user,
            full_name=full_name,
            address=address,
            phone=phone,
            created=timezone.now(),
            status='processing',
            total=0
        )

        total = 0
        for it in items:
            price = float(it.product.price)
            OrderItem.objects.create(order=order, product=it.product, price=price, quantity=it.quantity)
            total += price * it.quantity

        order.total = total
        order.save()

        # Очистка корзины
        CartItem.objects.filter(user=user).delete()

        # Сохранение id заказа в сессии
        request.session['last_order_id'] = order.id

        messages.success(request, "Ваш заказ успешно оформлен!")
        # Редирект на страницу имитации платежа
        return redirect('store:payment_success')
    
# Фейковая страница успеха оплаты: меняет статус 'processing'->'paid', показывает страницу успеха,
# затем перенаправляет на /orders/
def payment_success(request):
    last_order_id = request.session.get('last_order_id')
    if last_order_id:
        try:
            order = Order.objects.get(pk=last_order_id)
            # если ещё processing — пометим как paid
            if order.status == 'processing':
                order.status = 'paid'
                order.save()
        except Order.DoesNotExist:
            order = None
    else:
        order = None

    return render(request, 'payment_success.html', {'order': order})

# Orders: показывает историю заказов (для авторизованного пользователя — все его заказы,
# для гостя — последний заказ по сессии)
def orders(request):
    if request.user.is_authenticated:
        qs = Order.objects.filter(user=request.user).order_by('-created')
    else:
        last_order_id = request.session.get('last_order_id')
        qs = Order.objects.filter(pk=last_order_id) if last_order_id else Order.objects.none()
    return render(request, 'orders.html', {'orders': qs})

# Статические страницы
def about(request):
    return render(request, 'about.html')

def contact(request):
    return render(request, 'contact.html')

def contact_view(request):
    if request.method == "POST":
        name = request.POST.get("name")
        email = request.POST.get("email")
        subject = request.POST.get("subject")
        message = request.POST.get("message")

        ContactMessage.objects.create(
            name=name,
            email=email,
            subject=subject,
            message=message
        )

        messages.success(request, "Ваше сообщение успешно отправлено!")
        return redirect("store:contact")

    return render(request, "contact.html")

def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, f"Добро пожаловать, {user.username}!")
            return redirect("store:index")
        else:
            messages.error(request, "Неверное имя пользователя или пароль.")
    return render(request, "login.html")


# выход
def logout_view(request):
    logout(request)
    messages.info(request, "Вы вышли из системы.")
    return redirect("store:index")

def register_view(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, "Аккаунт создан! Теперь войдите в систему.")
            return redirect("store:login")
        else:
            messages.error(request, "Ошибка при регистрации. Проверьте введённые данные.")
    else:
        form = RegisterForm()
    return render(request, "register.html", {"form": form})


def sale_list(request):
    sales = Sale.objects.all()
    return render(request, 'sale_list.html', {'sales': sales})


def sale_detail(request, sale_id):
    sale = get_object_or_404(Sale, id=sale_id)
    products = sale.products.all()
    return render(request, 'sale_detail.html', {'sale': sale, 'products': products})