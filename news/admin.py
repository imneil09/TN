from django.contrib import admin
from .models import Article, Category, District

@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'district', 'created_at')
    list_filter = ('category', 'district', 'is_breaking')
    search_fields = ('title', 'content')

admin.site.register(Category)
admin.site.register(District)