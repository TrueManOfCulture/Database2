from django import forms
from .models import Produto, Usuario, Pedido, Stock, Promocao, PedidoProduto

class ProdutoForm(forms.ModelForm):
    class Meta:
        model = Produto
        fields = '__all__'

class UsuarioForm(forms.ModelForm):
    class Meta:
        model = Usuario
        fields = '__all__'

class PedidoForm(forms.ModelForm):
    class Meta:
        model = Pedido
        fields = '__all__'

class StockForm(forms.ModelForm):
    class Meta:
        model = Stock
        fields = '__all__'

class PromocaoForm(forms.ModelForm):
    class Meta:
        model = Promocao
        fields = '__all__'

class PedidoProdutoForm(forms.ModelForm):
    class Meta:
        model = PedidoProduto
        fields = '__all__'
