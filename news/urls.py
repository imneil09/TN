from django.urls import path
from . import views

# Note: app_name is disabled because templates use global names (e.g. 'home' instead of 'news:home')
# app_name = 'news' 

urlpatterns = [
    path('', views.home, name='home'),
    path('article/<slug:slug>/', views.article_detail, name='article_detail'),
    path('category/<slug:slug>/', views.category_detail, name='category_detail'),
]