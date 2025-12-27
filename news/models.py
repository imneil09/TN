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
    
    class Meta:
        verbose_name_plural = "Categories"

class District(models.Model):
    """Specific for Tripura Districts filter"""
    name = models.CharField(max_length=100) # e.g., West, North, Dhalai
    
    def __str__(self):
        return self.name

class Article(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, blank=True)
    subtitle = models.CharField(max_length=300, blank=True, null=True)
    content = models.TextField()
    image = models.ImageField(upload_to='news_images/')
    
    # Classification
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='articles')
    district = models.ForeignKey(District, on_delete=models.SET_NULL, null=True, blank=True, help_text="Only for Tripura news")
    
    # Metadata
    author = models.CharField(max_length=100, default="Tripura Now Bureau")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Feature Flags
    is_breaking = models.BooleanField(default=False, help_text="Shows in the top ticker")
    is_hero = models.BooleanField(default=False, help_text="Shows as the main big image on home")
    is_trending = models.BooleanField(default=False, help_text="Shows in trending section")

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title)
            # Simple logic to ensure unique slug (in production use a UUID or counter)
            self.slug = base_slug
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title
    
    class Meta:
        ordering = ['-created_at']