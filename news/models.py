from django.db import models
from django.utils.text import slugify

class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

class District(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

class Article(models.Model):
    title = models.CharField(max_length=255)
    slug = models.SlugField(unique=True, blank=True, max_length=255)
    subtitle = models.TextField(blank=True)
    content = models.TextField()  # HTML content from RaShi AI
    
    # --- Classification ---
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    district = models.ForeignKey(District, on_delete=models.SET_NULL, null=True, blank=True)
    
    # --- Deduplication & Source ---
    # Stores the visited URL so we don't visit it again
    source_url = models.URLField(max_length=1000, unique=True, null=True, blank=True)
    
    # --- Image Handling ---
    # Stores the real image URL found by the AI
    image_url = models.URLField(max_length=1000, blank=True, null=True)
    
    author = models.CharField(max_length=100, default="RraSHI AI")
    created_at = models.DateTimeField(auto_now_add=True)
    
    # --- Flags ---
    is_breaking = models.BooleanField(default=True)
    is_hero = models.BooleanField(default=False)
    is_trending = models.BooleanField(default=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

    # --- COMPATIBILITY LAYER ---
    # This allows {{ article.image.url }} to work in your templates
    # even though we are just storing a text URL string.
    @property
    def image(self):
        class ImageWrapper:
            def __init__(self, url): self.url = url
        # Logic: Use the real AI image if we have it, otherwise the placeholder
        return ImageWrapper(self.image_url or "https://source.unsplash.com/random/800x600/?news")