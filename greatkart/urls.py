from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from .views import home

urlpatterns = [
    path('admin/', include('admin_honeypot.urls', namespace='admin_honeypot')),
    path('myboss_account/', admin.site.urls),
    path('', home, name='home'),
    path('store/', include('store.urls')),
    path('cart/', include('cart.urls')),
    path('order/', include('orders.urls')),
    path('accounts/', include('accounts.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
