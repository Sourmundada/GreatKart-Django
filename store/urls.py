from django.urls import path
from store import views

urlpatterns = [
    path('', views.store, name='store'),
    path('c/<slug:category_slug>/', views.store, name='products_by_category'),
    path('c/<slug:category_slug>/<slug:product_slug>/', views.product_detail, name='product_detail'),
    path('s/', views.search, name='search'),
    path('submit_review/<int:product_id>/', views.submit_review, name='submit_review'),
]