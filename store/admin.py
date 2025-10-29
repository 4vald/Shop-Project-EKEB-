from django.contrib import admin
from .models import Category, Product, CartItem, Order, OrderItem, ContactMessage

from django.utils.html import format_html


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name',)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('title', 'price', 'stock', 'category', 'image_preview', 'updated')
    list_filter = ('category', 'updated')
    search_fields = ('title', 'description')
    prepopulated_fields = {'slug': ('title',)}

    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="60" height="60" style="object-fit:cover;border-radius:8px"/>', obj.image.url)
        return "—"
    image_preview.short_description = "Preview"


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('product', 'price', 'quantity', 'subtotal_display')

    def subtotal_display(self, obj):
        return f"{obj.subtotal():.2f}"
    subtotal_display.short_description = 'Subtotal'


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'full_name', 'status', 'total', 'created')
    list_filter = ('status', 'created')
    search_fields = ('full_name', 'phone')
    readonly_fields = ('created',)
    inlines = [OrderItemInline]


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ('user', 'product', 'quantity', 'added')
    list_filter = ('added',)
    search_fields = ('user__username', 'product__title')


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('order', 'product', 'price', 'quantity', 'subtotal_display')

    def subtotal_display(self, obj):
        return f"{obj.subtotal():.2f}"
    subtotal_display.short_description = 'Subtotal'


from django.contrib import admin
from .models import ContactMessage

@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ("name", "email", "subject", "created")
    search_fields = ("name", "email", "subject", "message")
    list_filter = ("created",)



from .models import HeroBanner

@admin.register(HeroBanner)
class HeroBannerAdmin(admin.ModelAdmin):
    list_display = ("id", "order", "active", "image")
    list_editable = ("order", "active")