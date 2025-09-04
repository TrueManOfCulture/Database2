from django.contrib import admin
from django.urls import path, include
from loja.views import home

urlpatterns = [
    path('', include('loja.urls')),
    path('django-admin/', admin.site.urls),
]
