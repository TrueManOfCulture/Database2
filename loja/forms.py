from django import forms
from django.forms import formset_factory
from django.db import connection
from .models import Produto, Usuario, Pedido, Stock, Tem2
from .mongodb_service import ProdutoService

produto_service = ProdutoService()

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
        fields = ['data_concluido']  # Remove 'status' from editable fields
        widgets = {
            'data_concluido': forms.DateInput(attrs={'type': 'date'}),
        }
        labels = {
            'data_concluido': 'Data de Conclusão',
        }

class PedidoProdutoForm(forms.Form):
    id_produto = forms.IntegerField(widget=forms.HiddenInput())
    nome_produto = forms.CharField(
        max_length=255, 
        required=False, 
        widget=forms.TextInput(attrs={'readonly': 'readonly', 'class': 'form-control'})
    )
    quantidade = forms.IntegerField(
        min_value=0,
        required=False,  # Make this not required to avoid validation errors
        widget=forms.NumberInput(attrs={'class': 'form-control', 'min': '0'})
    )
    remover = forms.BooleanField(required=False, widget=forms.CheckboxInput())

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.initial.get('id_produto'):
            try:
                produto = produto_service.get_produto(self.initial['id_produto'])
                self.initial['nome_produto'] = produto.get('nome', f'Produto #{self.initial["id_produto"]}')
            except:
                self.initial['nome_produto'] = f'Produto #{self.initial["id_produto"]}'

    def clean(self):
        cleaned_data = super().clean()
        quantidade = cleaned_data.get('quantidade')
        remover = cleaned_data.get('remover', False)
        
        # If removing, quantity doesn't matter
        if remover:
            return cleaned_data
            
        # If not removing, quantity must be positive
        if quantidade is not None and quantidade <= 0:
            raise forms.ValidationError("Quantidade deve ser maior que 0.")
            
        return cleaned_data

class NovoProdutoForm(forms.Form):
    id_produto = forms.ChoiceField(
        choices=[],
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Adicionar Produto'
    )
    quantidade = forms.IntegerField(
        min_value=1,
        initial=1,
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'min': '1'})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Get available products with stock
        try:
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT DISTINCT s.id_produto 
                    FROM stock s 
                    WHERE s.quantidade > 0
                """)
                produtos_com_stock = [row[0] for row in cursor.fetchall()]
            
            # Get product names from MongoDB
            choices = [('', 'Selecione um produto')]
            for produto_id in produtos_com_stock:
                try:
                    produto = produto_service.get_produto(produto_id)
                    nome = produto.get('nome', f'Produto #{produto_id}')
                    choices.append((produto_id, nome))
                except:
                    choices.append((produto_id, f'Produto #{produto_id}'))
            
            self.fields['id_produto'].choices = choices
        except:
            self.fields['id_produto'].choices = [('', 'Nenhum produto disponível')]

# Create formset for managing multiple products in an order
PedidoProdutoFormSet = formset_factory(
    PedidoProdutoForm, 
    extra=0, 
    can_delete=False
)

class StockForm(forms.ModelForm):
    id_produto = forms.ChoiceField(
        choices=[],
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Produto'
    )
    
    class Meta:
        model = Stock
        fields = ['id_produto', 'quantidade']
        widgets = {
            'quantidade': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
        }
        labels = {
            'quantidade': 'Quantidade',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Get available products from MongoDB
        try:
            produtos = produto_service.list_produtos()
            choices = [('', 'Selecione um produto')]
            for produto in produtos:
                choices.append((produto['_id'], produto.get('nome', f'Produto #{produto["_id"]}')))
            self.fields['id_produto'].choices = choices
        except:
            self.fields['id_produto'].choices = [('', 'Nenhum produto disponível')]

class SupplierProdutoStockForm(forms.Form):
    # Product fields
    nome = forms.CharField(
        max_length=255, 
        label='Nome do Produto',
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    descricao = forms.CharField(
        required=False,
        label='Descrição',
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 4})
    )
    preco = forms.DecimalField(
        max_digits=10, 
        decimal_places=2,
        label='Preço (€)',
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'})
    )
    categoria = forms.ChoiceField(
        required=False,
        choices=[],
        label='Categoria',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    marca = forms.CharField(
        max_length=255,
        required=False,
        label='Marca',
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    condicao = forms.ChoiceField(
        required=False,
        choices=[
            ('', 'Selecione a condição'),
            ('novo', 'Novo'),
            ('usado', 'Usado'),
            ('recondicionado', 'Recondicionado')
        ],
        label='Condição',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    detalhes_condicao = forms.CharField(
        required=False,
        label='Detalhes da Condição',
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3})
    )
    
    quantidade_stock = forms.IntegerField(
        min_value=0,
        initial=0,
        label='Quantidade em Stock',
        widget=forms.NumberInput(attrs={'class': 'form-control', 'min': '0'})
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Populate categories
        try:
            categorias = produto_service.get_categorias()
            choices = [('', 'Selecione uma categoria')]
            for cat in categorias:
                choices.append((cat, cat))
            self.fields['categoria'].choices = choices
        except:
            self.fields['categoria'].choices = [('', 'Nenhuma categoria disponível')]