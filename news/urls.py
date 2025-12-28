from django.urls import path
from . import views

# app_name = 'news'  # NOTE: Keep this commented out unless you update your templates to use 'news:home'

urlpatterns = [
    path('', views.home, name='home'),
    path('article/<slug:slug>/', views.article_detail, name='article_detail'),
    path('category/<slug:slug>/', views.category_detail, name='category_detail'),
]