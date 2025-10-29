from django.urls import path
from . import views

app_name = 'store'

urlpatterns = [
    path('', views.index, name='index'),
    path('product/<int:product_id>/', views.product_detail, name='product_detail'),
    path('add-to-cart/<int:pk>/', views.AddToCartView.as_view(), name='add_to_cart'),
    path('cart/', views.CartView.as_view(), name='cart'),
    path('cart/update/<int:pk>/', views.UpdateCartItemView.as_view(), name='update_cart'),
    path('checkout/', views.CheckoutView.as_view(), name='checkout'),
    path('payment/success/', views.payment_success, name='payment_success'),
    path('orders/', views.orders, name='orders'),
    path('about/', views.about, name='about'),
    path('contact/', views.contact_view, name='contact'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path("logout/", views.logout_view, name="logout"),
    path('cart/add/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
]

