from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import login as auth_login, logout as auth_logout, authenticate
from .models import Usuario, Pedido, Stock
from .forms import UsuarioForm, PedidoForm, StockForm
from .mongodb_service import ProdutoService
from django.db import connection
from django.contrib import messages
from bson import ObjectId

produto_service = ProdutoService()

# ==============================
# HOME
# ==============================
def home(request):
    search = request.GET.get("search")
    categoria = request.GET.get("categoria")
    avaliacao = request.GET.get("avaliacao")

    produtos = produto_service.list_produtos(
        search=search,
        categoria=categoria,
        avaliacao=avaliacao
    )

    categorias = produto_service.get_categorias()

    return render(request, "produto_list_cliente.html", {
        "produtos": produtos,
        "categorias": categorias
    })


# ==============================
# LOGIN / LOGOUT
# ==============================
def user_login(request):
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")

        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT id_usuario, tipo_usuario 
                FROM usuario 
                WHERE email = %s AND password = %s
            """, [email, password])
            user = cursor.fetchone()

        if user:
            user_id, tipo = user

            # Guardar o user na sessão (substituto do Django auth_login)
            request.session["user_id"] = user_id
            request.session["tipo_usuario"] = tipo

            # Redirecionar consoante o tipo
            if tipo == "cliente":
                return redirect("produto_list")   # página de produtos
            elif tipo == "fornecedor":
                return redirect("seller_page")    # página de fornecedor
        else:
            messages.error(request, "Email ou password inválidos.")
            return render(request, "login.html")

    return render(request, "login.html")

def user_logout(request):
    auth_logout(request)
    return redirect('home')

def user_register(request):
    if request.method == "POST":
        nome = request.POST["username"]
        email = request.POST["email"]
        password = request.POST["password1"]
        tipo_usuario = request.POST["tipo_usuario"]

        with connection.cursor() as cursor:
            if tipo_usuario == "cliente":
                genero = request.POST.get("genero")
                data_nascimento = request.POST.get("data_nascimento")
                morada = request.POST.get("morada")

                cursor.execute("""
                    SELECT criar_cliente(%s, %s, %s, %s, %s, %s)
                """, [nome, email, password, genero, data_nascimento, morada])

            elif tipo_usuario == "fornecedor":
                nif = request.POST.get("nif")

                cursor.execute("""
                    SELECT criar_fornecedor(%s, %s, %s, %s)
                """, [nome, email, password, nif])

        return redirect("login")

    return render(request, "register.html")

# ==============================
# USUARIO CRUD (apenas se quiseres gerir no painel)
# ==============================
def usuario_list(request):
    usuarios = Usuario.objects.all()
    return render(request, 'usuario_list.html', {'usuarios': usuarios})

def usuario_create(request):
    if request.method == 'POST':
        form = UsuarioForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('usuario_list')
    else:
        form = UsuarioForm()
    return render(request, 'usuario_form.html', {'form': form})

def usuario_update(request, pk):
    usuario = get_object_or_404(Usuario, pk=pk)
    if request.method == 'POST':
        form = UsuarioForm(request.POST, instance=usuario)
        if form.is_valid():
            form.save()
            return redirect('usuario_list')
    else:
        form = UsuarioForm(instance=usuario)
    return render(request, 'usuario_form.html', {'form': form})

def usuario_delete(request, pk):
    usuario = get_object_or_404(Usuario, pk=pk)
    if request.method == 'POST':
        usuario.delete()
        return redirect('usuario_list')
    return render(request, 'usuario_confirm_delete.html', {'usuario': usuario})


# ==============================
# PEDIDO CRUD
# ==============================
def pedido_list(request):
    with connection.cursor() as cur:
        cur.execute("SELECT id_pedido, status, data_efetuado, id_produto, quantidade FROM vw_cliente_pedidos WHERE id_cliente = %s", [request.user.id])
        pedidos = cur.fetchall()
    return render(request, "cliente_pedidos.html", {"pedidos": pedidos})

def pedido_create(request):
    if request.method == 'POST':
        form = PedidoForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('pedido_list')
    else:
        form = PedidoForm()
    return render(request, 'pedido_form.html', {'form': form})

def pedido_update(request, pk):
    pedido = get_object_or_404(Pedido, pk=pk)
    if request.method == 'POST':
        form = PedidoForm(request.POST, instance=pedido)
        if form.is_valid():
            form.save()
            return redirect('pedido_list')
    else:
        form = PedidoForm(instance=pedido)
    return render(request, 'pedido_form.html', {'form': form})

def pedido_delete(request, pk):
    pedido = get_object_or_404(Pedido, pk=pk)
    if request.method == 'POST':
        pedido.delete()
        return redirect('pedido_list')
    return render(request, 'pedido_confirm_delete.html', {'pedido': pedido})

def pedido_fornecedor(request):
    fornecedor_id = request.user.id  # mapped to FORNECEDOR.ID_FORNECEDOR
    
    with connection.cursor() as cur:
        cur.execute("SELECT * FROM pedidos_por_fornecedor(%s)", [fornecedor_id])
        rows = cur.fetchall()
    
    # Group products by order
    pedidos_dict = defaultdict(list)
    pedidos_info = {}
    for row in rows:
        id_pedido, id_cliente, status, data_efetuado, id_produto, quantidade = row
        pedidos_info[id_pedido] = {
            "id_cliente": id_cliente,
            "status": status,
            "data_efetuado": data_efetuado
        }
        pedidos_dict[id_pedido].append({
            "id_produto": id_produto,
            "quantidade": quantidade
        })
    
    # Combine info and products
    pedidos = []
    for id_pedido, produtos in pedidos_dict.items():
        pedidos.append({
            "id_pedido": id_pedido,
            "id_cliente": pedidos_info[id_pedido]["id_cliente"],
            "status": pedidos_info[id_pedido]["status"],
            "data_efetuado": pedidos_info[id_pedido]["data_efetuado"],
            "produtos": produtos
        })

    return render(request, "fornecedor_pedidos.html", {"pedidos": pedidos})

# ==============================
# STOCK CRUD
# ==============================
def stock_list(request):
    stocks = Stock.objects.all()
    return render(request, 'stock_list.html', {'stocks': stocks})

def stock_create(request):
    if request.method == 'POST':
        form = StockForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('stock_list')
    else:
        form = StockForm()
    return render(request, 'stock_form.html', {'form': form})

def stock_update(request, pk):
    stock = get_object_or_404(Stock, pk=pk)
    if request.method == 'POST':
        form = StockForm(request.POST, instance=stock)
        if form.is_valid():
            form.save()
            return redirect('stock_list')
    else:
        form = StockForm(instance=stock)
    return render(request, 'stock_form.html', {'form': form})

def stock_delete(request, pk):
    stock = get_object_or_404(Stock, pk=pk)
    if request.method == 'POST':
        stock.delete()
        return redirect('stock_list')
    return render(request, 'stock_confirm_delete.html', {'stock': stock})

def produto_list(request):
    produtos = produto_service.list_produtos()
    return render(request, 'produto_list.html', {'produtos': produtos})

def produto_create(request):
    if request.method == 'POST':
        produto_data = {
            "nome": request.POST.get("nome"),
            "descricao": request.POST.get("descricao"),
            "preco": float(request.POST.get("preco")),
            "imagens": request.POST.getlist("imagens")  # exemplo se for lista
        }
        produto_service.create_produto(produto_data)
        return redirect('produto_list')
    return render(request, 'produto_form.html')

def produto_update(request, produto_id):
    produto = produto_service.get_produto(produto_id)
    if request.method == 'POST':
        update_data = {
            "nome": request.POST.get("nome"),
            "descricao": request.POST.get("descricao"),
            "preco": float(request.POST.get("preco")),
            "imagens": request.POST.getlist("imagens")
        }
        produto_service.update_produto(produto_id, update_data)
        return redirect('produto_list')
    return render(request, 'produto_form.html', {'produto': produto})

def produto_delete(request, produto_id):
    produto = produto_service.get_produto(produto_id)
    if request.method == 'POST':
        produto_service.delete_produto(produto_id)
        return redirect('produto_list')
    return render(request, 'produto_confirm_delete.html', {'produto': produto})

def produto_buy(request, pk):
    user_id = request.user.id  # Django user must be mapped to CLIENTE.ID_CLIENTE
    
    # 1. Create PEDIDO (order)
    conn = psycopg2.connect(
        dbname="techmart", user="postgres", password="123", host="localhost"
    )
    cur = conn.cursor()

    # Insert new pedido
    cur.execute("""
        INSERT INTO PEDIDO (ID_CLIENTE, DATA_EFETUADO, STATUS)
        VALUES (%s, %s, %s)
        RETURNING ID_PEDIDO
    """, (user_id, datetime.date.today(), "Pendente"))
    pedido_id = cur.fetchone()[0]

    # 2. Insert into TEM2 (order-product link)
    cur.execute("""
        INSERT INTO TEM2 (ID_PEDIDO, ID_PRODUTO, QUANTIDADE)
        VALUES (%s, %s, %s)
    """, (pedido_id, int(ObjectId(pk).binary.hex(), 16) % (2**31), 1))
    # ⚠️ Mongo _id is an ObjectId, not int → you must decide how to map
    # One approach: keep ObjectId as string in a separate table or hash to int

    conn.commit()
    cur.close()
    conn.close()

    # 3. Redirect to order confirmation page
    return redirect("cliente_pedidos")