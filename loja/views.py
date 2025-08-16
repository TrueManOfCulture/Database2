from django.shortcuts import render, redirect, get_object_or_404
from .models import Produto, Usuario, Pedido, Stock, Promocao, PedidoProduto
from .forms import ProdutoForm, UsuarioForm, PedidoForm, StockForm, PromocaoForm, PedidoProdutoForm

def produto_list(request):
    produtos = Produto.objects.all()
    return render(request, 'produto_list.html', {'produtos': produtos})

def produto_create(request):
    if request.method == 'POST':
        form = ProdutoForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('produto_list')
    else:
        form = ProdutoForm()
    return render(request, 'produto_form.html', {'form': form})

def produto_update(request, pk):
    produto = get_object_or_404(Produto, pk=pk)
    if request.method == 'POST':
        form = ProdutoForm(request.POST, instance=produto)
        if form.is_valid():
            form.save()
            return redirect('produto_list')
    else:
        form = ProdutoForm(instance=produto)
    return render(request, 'produto_form.html', {'form': form})

def produto_delete(request, pk):
    produto = get_object_or_404(Produto, pk=pk)
    if request.method == 'POST':
        produto.delete()
        return redirect('produto_list')
    return render(request, 'produto_confirm_delete.html', {'produto': produto})

def home(request):
    return render(request, 'home.html')

def login(request):
    if request.method == 'POST':
        form = AuthenticationForm(request=request, data=request.POST)
        if form.is_valid():
            # Se os dados de login estiverem corretos, autentica o usuário
            user = form.get_user()
            login(request, user)
            return redirect('home')  # Redireciona para a página inicial após login
        else:
            return render(request, 'login.html', {'form': form})
    else:
        form = AuthenticationForm()
    return render(request, 'login.html', {'form': form})