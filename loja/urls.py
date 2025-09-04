from django.urls import path

from .views import *

urlpatterns = [
    path('', home, name='home'),
    path('login/', user_login, name='login'),
    path('logout/', user_logout, name='logout'),
    path("register/", user_register, name="register"),
    

    path('produtos/novo/', produto_create, name='produto_create'),
    path('produtos/editar/<str:produto_id>/', produto_update, name='produto_update'),
    path('produtos/deletar/<str:produto_id>/', produto_delete, name='produto_delete'),
    path('produtos/list/', produto_list, name='produto_list'),
    path('produto/<str:produto_id>/', produto_detail, name='produto_detail'),
    path('produto/<str:produto_id>/avaliacao/', submit_avaliacao, name='submit_avaliacao'),
    
    path('pedidos/', pedido_list, name='pedido_list'),
    path('pedidos/novo/', pedido_create, name='pedido_create'),
    path('pedidos/confirmar/<int:pk>/', pedido_confirmar, name='pedido_confirmar'),
    path('pedidos/editar/<int:pk>/', pedido_update, name='pedido_update'),
    path('pedidos/deletar/<int:pk>/', pedido_delete, name='pedido_delete'),
    path("pedido/adicionar/<str:produto_id>/", add_produto, name="add_produto"),
    
    path("supplier/panel/", fornecedor_page, name="fornecedor_page"),
    path('supplier/produtos/', supplier_produto_list, name='supplier_produto_list'),
    path('supplier/pedidos/', supplier_pedidos, name='supplier_pedidos'),
    path('supplier/promocoes/', supplier_promocoes, name='supplier_promocoes'),
    path('supplier/promocoes/nova/', promocao_form, name='promocao_create'),
    path('supplier/promocoes/editar/<str:promocao_id>/', promocao_form, name='promocao_edit'),
    path('supplier/promocoes/remover/<str:promocao_id>/', promocao_delete, name='promocao_delete'),

    path('admin/home/', admin_home, name='admin_home'),
    path('admin/users/', admin_users, name='admin_users'),
    path('admin/users/create/', admin_user_create, name='admin_user_create'),
    path('admin/users/edit/<int:user_id>/', admin_user_edit, name='admin_user_edit'),  
    path('admin/users/delete/<int:user_id>/', admin_user_delete, name='admin_user_delete'),
]
