from django.urls import path
from . import views

app_name = 'store'

urlpatterns = [
    # главная
    path('', views.index, name='index'),

    # товары
    path('product/<int:product_id>/', views.product_detail, name='product_detail'),
    path('product/<int:product_id>/review/', views.add_review, name='add_review'),

    # корзина и заказы
    path('add-to-cart/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/', views.CartView.as_view(), name='cart'),
    path('cart/update/<int:pk>/', views.UpdateCartItemView.as_view(), name='update_cart'),
    path('cart/update-quantity/', views.update_cart_quantity, name='update_cart_quantity'),
    path('checkout/', views.CheckoutView.as_view(), name='checkout'),
    path('payment/success/', views.payment_success, name='payment_success'),
    path('orders/', views.orders, name='orders'),

    # страницы
    path('about/', views.about, name='about'),
    path('contact/', views.contact_view, name='contact'),

    # аутентификация
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),

    # акции
    path('sale/', views.sale_list, name='sale_list'),
    path('sale/<int:sale_id>/', views.sale_detail, name='sale_detail'),

    # поиск
    path('search/', views.search_products, name='search_products'),

    #профиль
    path('profile/', views.profile_view, name='profile'),
]
