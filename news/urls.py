from django.urls import path
from . import views

urlpatterns = [
    # Homepage (Static Ads)
    path('', views.home, name='home'),
    
    # Article Detail Page (Google Ads)
    # Uses a 'slug' to find the specific article (e.g., /article/tripura-it-park-announced/)
    path('article/<slug:slug>/', views.article_detail, name='article_detail'),
    
    # Category Page (Google Ads)
    # e.g., /category/tripura/ or /category/northeast/
    path('category/<slug:slug>/', views.category_detail, name='category_detail'),
    path('info/', views.company_info, name='company_info'),

]