import os
from django.core.management.base import BaseCommand
from store.models import Product, Category
from django.core.files.base import ContentFile
import requests
from django.conf import settings

PRODUCTS = [
    {
        "title": "Беспроводные наушники X100",
        "slug": "x100",
        "description": "Премиальные беспроводные наушники с шумоподавлением и 30 часами работы.",
        "price": 59990.00,
        "category": "Аудио",
        "image_url": "https://images.unsplash.com/photo-1518444023048-8cf3d7f2b5c3?auto=format&fit=crop&w=800&q=80"
    },
    {
        "title": "Умные часы S7",
        "slug": "s7",
        "description": "Умные часы с пульсометром, GPS и автономностью 7 дней.",
        "price": 129990.00,
        "category": "Гаджеты",
        "image_url": "https://images.unsplash.com/photo-1518444023048-6f6f3f2b5c3d?auto=format&fit=crop&w=800&q=80"
    },
    {
        "title": "Портативная колонка Boom",
        "slug": "boom",
        "description": "Мощная влагозащищённая колонка с 12 часами воспроизведения.",
        "price": 39990.00,
        "category": "Аудио",
        "image_url": "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?auto=format&fit=crop&w=800&q=80"
    },
    {
        "title": "Ноутбук ProLite 15",
        "slug": "prolite15",
        "description": "Лёгкий и мощный ноутбук для разработчиков и креативщиков.",
        "price": 259990.00,
        "category": "Ноутбуки",
        "image_url": "https://images.unsplash.com/photo-1517336714731-489689fd1ca8?auto=format&fit=crop&w=1000&q=80"
    },
]
class Command(BaseCommand):
    help = 'Seed initial products with images'

    def handle(self, *args, **options):
        media_root = getattr(settings, 'MEDIA_ROOT', None)
        if not media_root:
            self.stdout.write(self.style.ERROR('MEDIA_ROOT is not set in settings.'))
            return

        for p in PRODUCTS:
            cat, _ = Category.objects.get_or_create(name=p['category'], slug=p['category'].lower())
            prod, created = Product.objects.get_or_create(slug=p['slug'], defaults={
                'title': p['title'],
                'description': p['description'],
                'price': p['price'],
                'stock': 50,
                'category': cat,
            })
            # fetch image
            try:
                r = requests.get(p['image_url'], timeout=10)
                if r.status_code == 200:
                    filename = f"{p['slug']}.jpg"
                    prod.image.save(filename, ContentFile(r.content), save=True)
                    self.stdout.write(self.style.SUCCESS(f"Saved image for {p['title']}"))
            except Exception as e:
                self.stdout.write(self.style.WARNING(f"Couldn't download image for {p['title']}: {e}"))
            prod.save()

        self.stdout.write(self.style.SUCCESS('Seeded products'))
