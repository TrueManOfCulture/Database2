from django.contrib import admin
from .models import Usuario, Produto, Stock, Pedido, Promocao, PedidoProduto

# Register the models
admin.site.register(Usuario)
admin.site.register(Produto)
admin.site.register(Stock)
admin.site.register(Pedido)
admin.site.register(Promocao)
admin.site.register(PedidoProduto)
