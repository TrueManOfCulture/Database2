from django.contrib import admin
from django.urls import path, include
from loja.views import home

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('loja.urls')),
]
