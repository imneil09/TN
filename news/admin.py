from django.contrib import admin
from .models import Category, District, Article

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}

@admin.register(District)
class DistrictAdmin(admin.ModelAdmin):
    list_display = ('name',)

@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'district', 'is_breaking', 'is_hero', 'created_at')
    list_filter = ('category', 'is_breaking', 'district', 'created_at')
    search_fields = ('title', 'content')
    prepopulated_fields = {'slug': ('title',)}
    list_editable = ('is_breaking', 'is_hero') # Edit these directly from the list!