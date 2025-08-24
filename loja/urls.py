from django.urls import path
from .views import (
    home, user_login, user_logout, user_register,

    produto_list, produto_create, produto_update, produto_delete, produto_buy,

    pedido_list, pedido_create, pedido_update, pedido_delete,

    stock_list, stock_create, stock_update, stock_delete,
)

urlpatterns = [
    # Core
    path('', produto_list, name='produto_list'),  # Default view
    path('home/', home, name='home'),
    path('login/', user_login, name='login'),
    path('logout/', user_logout, name='logout'),
    path("register/", user_register, name="register"),

    path('produtos/novo/', produto_create, name='produto_create'),
    path('produtos/editar/<str:produto_id>/', produto_update, name='produto_update'),
    path('produtos/deletar/<str:produto_id>/', produto_delete, name='produto_delete'),
    path('produtos/comprar/<str:pk>/', produto_buy, name='produto_buy'),

    path('pedidos/', pedido_list, name='pedido_list'),
    path('pedidos/novo/', pedido_create, name='pedido_create'),
    path('pedidos/editar/<int:pk>/', pedido_update, name='pedido_update'),
    path('pedidos/deletar/<int:pk>/', pedido_delete, name='pedido_delete'),
    path("pedido/adicionar/<str:produto_id>/", add_pedido, name="add_pedido"),

    path('stock/', stock_list, name='stock_list'),
    path('stock/novo/', stock_create, name='stock_create'),
    path('stock/editar/<int:pk>/', stock_update, name='stock_update'),
    path('stock/deletar/<int:pk>/', stock_delete, name='stock_delete'),
]
