from django.db import models
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

User = get_user_model()


# --------------------------
# Категории товаров
# --------------------------
class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)

    def __str__(self):
        return self.name


# --------------------------
# Товары
# --------------------------
class Product(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField(default=0)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    image = models.ImageField(upload_to='products/', blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    @property
    def active_sale(self):
        """Возвращает активную акцию, если товар участвует в ней."""
        return self.sales.first() if self.sales.exists() else None

    @property
    def discounted_price(self):
        """Цена со скидкой, если есть активная акция."""
        sale = self.active_sale
        if sale and sale.discount_percent > 0:
            discount = (self.price * sale.discount_percent) / 100
            return self.price - discount
        return self.price


# --------------------------
# Элементы корзины
# --------------------------
class CartItem(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    session_key = models.CharField(max_length=40, blank=True, null=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    added = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'product', 'session_key')

    def subtotal(self):
        return self.product.price * self.quantity

    def __str__(self):
        return f"{self.product.title} x {self.quantity}"


# --------------------------
# Заказы
# --------------------------
class Order(models.Model):
    STATUS_CHOICES = (
        ('new', 'New'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('cancelled', 'Cancelled'),
    )

    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    full_name = models.CharField(max_length=200)
    address = models.TextField()
    phone = models.CharField(max_length=20)
    created = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new')
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def __str__(self):
        return f"Order #{self.id} ({self.status})"


# --------------------------
# Товары в заказе
# --------------------------
class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)           # цена со скидкой
    quantity = models.PositiveIntegerField(default=1)
    original_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount_percent = models.PositiveIntegerField(default=0)

    def subtotal(self):
        return (self.product.discounted_price if hasattr(self.product, 'discounted_price') else self.product.price) * self.quantity


    def __str__(self):
        return f"{self.product} x {self.quantity}"
# --------------------------
# Контактные сообщения
# --------------------------
class ContactMessage(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    subject = models.CharField(max_length=200)
    message = models.TextField()
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} — {self.subject}"


# --------------------------
# Акции (Sale)
# --------------------------
class Sale(models.Model):
    title = models.CharField(max_length=255, verbose_name="Название акции")
    description = models.TextField(blank=True, verbose_name="Описание")
    discount_percent = models.PositiveIntegerField(default=0, verbose_name="Скидка (%)")
    products = models.ManyToManyField('Product', related_name='sales', verbose_name="Товары")
    image = models.ImageField(upload_to='sales/', blank=True, null=True, verbose_name="Изображение баннера")

    def __str__(self):
        return f"{self.title} (-{self.discount_percent}%)"

    def get_absolute_url(self):
        return reverse('store:sale_detail', args=[self.id])


# --------------------------
# Баннеры
# --------------------------
class HeroBanner(models.Model):
    image = models.ImageField(upload_to='banners/')
    order = models.PositiveIntegerField(default=0)
    active = models.BooleanField(default=True)
    sale = models.ForeignKey('Sale', on_delete=models.SET_NULL, null=True, blank=True, related_name='banners')

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"Баннер {self.pk} (порядок {self.order})"
class Review(models.Model):
    product = models.ForeignKey('Product', on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.PositiveSmallIntegerField(default=5)
    text = models.TextField(blank=True)
    image = models.ImageField(upload_to='review_images/', blank=True, null=True)  # <-- добавлено
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Отзыв от {self.user.username} для {self.product.title}"

# --------------------------
# Профиль пользователя
# --------------------------
class UserProfile(models.Model):
    GENDER_CHOICES = (
        ('male', 'Мужской'),
        ('female', 'Женский'),
        ('other', 'Другой'),
    )

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    first_name = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100, blank=True)
    city = models.CharField(max_length=100, blank=True)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, blank=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)  # <--- добавлено

    def __str__(self):
        return f"Профиль {self.user.username}"



@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()
