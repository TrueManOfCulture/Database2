from django.urls import path
from .views import produto_list, produto_create, produto_update, produto_delete, login, home

urlpatterns = [
    path('', produto_list, name='produto_list'),  # This makes /produtos/ the default view
    path('login/', login, name='login'),  # URL para acessar o login
    path('home/', home, name='home'),  # Página inicial após o login
    path('novo/', produto_create, name='produto_create'),
    path('editar/<int:pk>/', produto_update, name='produto_update'),
    path('deletar/<int:pk>/', produto_delete, name='produto_delete'),
]

