from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login as auth_login, logout as auth_logout, authenticate
from .models import Usuario, Pedido, Stock
from .forms import UsuarioForm, PedidoForm, StockForm,PedidoProdutoFormSet, NovoProdutoForm
from .mongodb_service import ProdutoService
from django.db import connection
from django.contrib import messages
from bson import ObjectId
from datetime import datetime
from collections import defaultdict

produto_service = ProdutoService()

def home(request):
    search = request.GET.get("search")
    categoria = request.GET.get("categoria")
    avaliacao = request.GET.get("avaliacao")

    produtos = produto_service.list_produtos(search=search, categoria=categoria, avaliacao=avaliacao)
    categorias = produto_service.get_categorias()
    
    # Get supplier names for all products
    produto_ids = [produto["_id"] for produto in produtos]
    
    # Create a mapping of product IDs to supplier names
    fornecedor_map = {}
    if produto_ids:
        with connection.cursor() as cursor:
            placeholders = ','.join(['%s'] * len(produto_ids))
            cursor.execute(f"""
                SELECT s.id_produto, u.nome 
                FROM stock s
                JOIN usuario u ON s.id_fornecedor = u.id_usuario
                WHERE s.id_produto IN ({placeholders})
            """, produto_ids)
            
            for id_produto, nome in cursor.fetchall():
                fornecedor_map[id_produto] = nome

    for produto in produtos:
        promocao_ativa = produto_service.get_promocao_ativa(produto["_id"])
        if promocao_ativa:
            produto["promocao"] = promocao_ativa
            produto["preco_promocional"] = produto_service.calcular_preco_promocional(
                produto["preco"], promocao_ativa
            )
        
        # Add supplier name to product
        produto["fornecedor_nome"] = fornecedor_map.get(produto["_id"], "Fornecedor Desconhecido")

    ratings = [5, 4, 3, 2, 1]

    return render(request, "home.html", {
        "produtos": produtos,
        "categorias": categorias,
        "ratings": ratings
    })


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
                return redirect("home")   # página de produtos
            elif tipo == "fornecedor":
                return redirect("fornecedor_page")    # página de fornecedor
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

def fornecedor_page(request):
    return render(request, "fornecedor/fornecedor_page.html")

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


def pedido_list(request):
    user_id = request.session.get("user_id")
    if not user_id:
        messages.error(request, "Faça login para ver seus pedidos.")
        return redirect("login")
    
    with connection.cursor() as cur:
        cur.execute("SELECT id_pedido, status, data_efetuado, id_produto, quantidade FROM vw_cliente_pedidos WHERE id_cliente = %s", [user_id])
        rows = cur.fetchall()
    
    # Group products by order and fetch product names
    pedidos_dict = defaultdict(list)
    pedidos_info = {}
    
    for row in rows:
        id_pedido, status, data_efetuado, id_produto, quantidade = row
        pedidos_info[id_pedido] = {
            "status": status,
            "data_efetuado": data_efetuado
        }
        
        # Get product name from MongoDB
        try:
            produto = produto_service.get_produto(id_produto)
            nome_produto = produto.get("nome", f"Produto #{id_produto}")
        except:
            nome_produto = f"Produto #{id_produto}"
        
        pedidos_dict[id_pedido].append({
            "id_produto": id_produto,
            "nome_produto": nome_produto,
            "quantidade": quantidade
        })
    
    # Combine info and products
    pedidos = []
    for id_pedido, produtos in pedidos_dict.items():
        pedidos.append({
            "id_pedido": id_pedido,  # Changed from ID_PEDIDO to id_pedido
            "status": pedidos_info[id_pedido]["status"],
            "data_efetuado": pedidos_info[id_pedido]["data_efetuado"],
            "produtos": produtos
        })
    
    return render(request, "pedido_list.html", {"pedidos": pedidos})

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
    
    # Check if the user has permission to edit this order
    user_id = request.session.get("user_id")
    if not user_id or pedido.id_cliente_id != int(user_id):
        messages.error(request, "Você não tem permissão para editar este pedido.")
        return redirect('pedido_list')
    
    # Only allow editing if order is still pending
    if pedido.status not in ['Pendente', 'Processando']:
        messages.error(request, "Este pedido não pode mais ser editado.")
        return redirect('pedido_list')
    
    # Get current products in the order
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT id_produto, quantidade 
            FROM tem2 
            WHERE id_pedido = %s
        """, [pedido.id_pedido])
        produtos_atuais = cursor.fetchall()
    
    # Prepare initial data for formset
    initial_data = []
    for id_produto, quantidade in produtos_atuais:
        try:
            produto = produto_service.get_produto(id_produto)
            nome_produto = produto.get('nome', f'Produto #{id_produto}')
        except:
            nome_produto = f'Produto #{id_produto}'
        
        initial_data.append({
            'id_produto': id_produto,
            'nome_produto': nome_produto,
            'quantidade': quantidade,
            'remover': False
        })
    
    if request.method == 'POST':
        pedido_form = PedidoForm(request.POST, instance=pedido)
        produto_formset = PedidoProdutoFormSet(request.POST, initial=initial_data)
        novo_produto_form = NovoProdutoForm(request.POST)
        if not pedido_form.is_valid():
            print("Pedido form errors:", pedido_form.errors)
        if not produto_formset.is_valid():
            print("Produto formset errors:", produto_formset.errors)
            for i, form in enumerate(produto_formset.forms):
                if form.errors:
                    print(f"Form {i} errors:", form.errors)
        
        pedido_form_valid = pedido_form.is_valid()
        produto_formset_valid = produto_formset.is_valid()
        
        if pedido_form_valid and produto_formset_valid:
            try:
                pedido_form.save()
                for form in produto_formset:
                    if form.cleaned_data and not form.cleaned_data.get('DELETE', False):
                        id_produto = form.cleaned_data['id_produto']
                        quantidade = form.cleaned_data['quantidade']
                        remover = form.cleaned_data.get('remover', False)
                            
                        if remover or quantidade == 0:
                            with connection.cursor() as cursor:
                                cursor.execute("""
                                    DELETE FROM tem2 
                                    WHERE id_pedido = %s AND id_produto = %s
                                """, [pedido.id_pedido, id_produto])
                        else:
                            with connection.cursor() as cursor:
                                cursor.execute("""
                                    SELECT quantidade FROM stock 
                                    WHERE id_produto = %s
                                """, [id_produto])
                                stock_result = cursor.fetchone()
                                
                                if stock_result and stock_result[0] >= quantidade:
                                    cursor.execute("""
                                        UPDATE tem2 
                                        SET quantidade = %s 
                                        WHERE id_pedido = %s AND id_produto = %s
                                    """, [quantidade, pedido.id_pedido, id_produto])
                                else:
                                    raise ValueError(f'Stock insuficiente para produto {id_produto}')
                
                if novo_produto_form.is_valid():
                    novo_id_produto_str = novo_produto_form.cleaned_data.get('id_produto')
                    nova_quantidade = novo_produto_form.cleaned_data.get('quantidade')
                    
                    if novo_id_produto_str and nova_quantidade and nova_quantidade > 0:
                        try:
                            novo_id_produto = int(novo_id_produto_str)
                            
                            with connection.cursor() as cursor:
                                cursor.execute("""
                                    SELECT quantidade FROM tem2 
                                    WHERE id_pedido = %s AND id_produto = %s
                                """, [pedido.id_pedido, novo_id_produto])
                                existing = cursor.fetchone()
                                
                                # Check stock availability
                                cursor.execute("""
                                    SELECT quantidade FROM stock 
                                    WHERE id_produto = %s
                                """, [novo_id_produto])
                                stock_result = cursor.fetchone()
                                
                                if not stock_result:
                                    raise ValueError(f'Produto {novo_id_produto} não encontrado em stock')
                                
                                required_stock = nova_quantidade
                                if existing:
                                    required_stock += existing[0]
                                
                                if stock_result[0] >= required_stock:
                                    if existing:
                                        cursor.execute("""
                                            UPDATE tem2 
                                            SET quantidade = quantidade + %s 
                                            WHERE id_pedido = %s AND id_produto = %s
                                        """, [nova_quantidade, pedido.id_pedido, novo_id_produto])
                                    else:
                                        # Insert new product
                                        cursor.execute("""
                                            INSERT INTO tem2 (id_pedido, id_produto, quantidade) 
                                            VALUES (%s, %s, %s)
                                        """, [pedido.id_pedido, novo_id_produto, nova_quantidade])
                                else:
                                    raise ValueError(f'Stock insuficiente para produto {novo_id_produto}')
                        except ValueError as ve:
                            raise ve
                        except Exception as e:
                            print(f"Error processing new product: {e}")
                            
                with connection.cursor() as cursor:
                    cursor.execute("""
                        SELECT COUNT(*) FROM tem2 WHERE id_pedido = %s
                    """, [pedido.id_pedido])
                    produto_count = cursor.fetchone()[0]
                    
                    if produto_count == 0:
                        # If no products left, delete the order
                        cursor.execute("""
                            DELETE FROM pedido WHERE id_pedido = %s
                        """, [pedido.id_pedido])
                        messages.success(request, "Pedido removido pois não possui mais produtos.")
                        return redirect('pedido_list')
                
                messages.success(request, "Pedido atualizado com sucesso!")
                return redirect('pedido_list')
                
            except ValueError as e:
                messages.error(request, str(e))
            except Exception as e:
                messages.error(request, f"Erro ao atualizar pedido: {str(e)}")
        else:
            # More specific error messages
            if not pedido_form_valid:
                messages.error(request, "Erro no formulário do pedido. Verifique os dados.")
            if not produto_formset_valid:
                messages.error(request, "Erro no formulário de produtos. Verifique as quantidades.")
    
    else:
        pedido_form = PedidoForm(instance=pedido)
        produto_formset = PedidoProdutoFormSet(initial=initial_data)
        novo_produto_form = NovoProdutoForm()
    
    return render(request, 'pedido_form.html', {
        'pedido': pedido,
        'pedido_form': pedido_form,
        'produto_formset': produto_formset,
        'novo_produto_form': novo_produto_form,
    })
def pedido_delete(request, pk):
    pedido = get_object_or_404(Pedido, pk=pk)
    if request.method == 'POST':
        pedido.delete()
        return redirect('pedido_list')
    return render(request, 'pedido_confirm_delete.html', {'pedido': pedido})


def produto_list(request):
    produtos = produto_service.list_produtos()
    return render(request, 'produto_list.html', {'produtos': produtos})

def produto_create(request):
    supplier_id = request.session.get("user_id")
    if not supplier_id or request.session.get("tipo_usuario") != "fornecedor":
        messages.error(request, "Acesso negado. Apenas fornecedores podem criar produtos.")
        return redirect("login")
    
    if request.method == 'POST':
        with connection.cursor() as cursor:
            cursor.execute("SELECT nextval('produto_id_seq')")
            new_id = str(cursor.fetchone()[0])
            
        produto_data = {
            "_id": int(new_id),
            "nome": request.POST.get("nome"),
            "descricao": request.POST.get("descricao"),
            "preco": float(request.POST.get("preco")),
            "categoria": request.POST.get("categoria", ""),
            "marca": request.POST.get("marca", ""),
            "condicao": request.POST.get("condicao", ""),
            "detalhes_condicao": request.POST.get("detalhes_condicao", ""),
            "fornecedor_id": int(supplier_id)
        }
        
        try:
            # Create product in MongoDB
            produto_service.create_produto(produto_data)
            
            # Add to stock table with the specified quantity
            quantidade_stock = int(request.POST.get("quantidade_stock", 0))
            with connection.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO stock (id_fornecedor, id_produto, quantidade)
                    VALUES (%s, %s, %s)
                """, [supplier_id, new_id, quantidade_stock])
            
            messages.success(request, "Produto criado com sucesso!")
            return redirect('supplier_produto_list')
            
        except Exception as e:
            messages.error(request, f"Erro ao criar produto: {str(e)}")
    
    categorias = produto_service.get_categorias()
    return render(request, 'fornecedor/produto_form.html', {
        'categorias': categorias,
        'is_edit': False
    })
def produto_update(request, produto_id):
    try:
        produto_id = int(produto_id)
    except (ValueError, TypeError):
        messages.error(request, "ID do produto inválido.")
        return redirect('supplier_produto_list')
    
    produto = produto_service.get_produto(produto_id)
    if not produto:
        messages.error(request, "Produto não encontrado.")
        return redirect('supplier_produto_list')
    
    supplier_id = request.session.get("user_id")
    if not supplier_id or request.session.get("tipo_usuario") != "fornecedor":
        messages.error(request, "Acesso negado. Apenas fornecedores podem editar produtos.")
        return redirect("login")
    
    # Get current stock info
    stock_atual = None
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT quantidade, ultimo_update 
            FROM stock 
            WHERE id_produto = %s AND id_fornecedor = %s
        """, [produto_id, supplier_id])
        stock_result = cursor.fetchone()
        if stock_result:
            stock_atual = {
                'quantidade': stock_result[0],
                'ultimo_update': stock_result[1]
            }
        else:
            messages.error(request, "Você não tem permissão para editar este produto.")
            return redirect('supplier_produto_list')
    
    if request.method == 'POST':
        try:
            # Update product in MongoDB
            update_data = {
                "nome": request.POST.get("nome"),
                "descricao": request.POST.get("descricao"),
                "preco": float(request.POST.get("preco")),
                "categoria": request.POST.get("categoria", ""),
                "marca": request.POST.get("marca", ""),
                "condicao": request.POST.get("condicao", ""),
                "detalhes_condicao": request.POST.get("detalhes_condicao", "")
            }
            
            produto_service.update_produto(produto_id, update_data)
            
            # Update stock quantity
            nova_quantidade = int(request.POST.get("quantidade_stock", 0))
            with connection.cursor() as cursor:
                cursor.execute("""
                    UPDATE stock 
                    SET quantidade = %s, ultimo_update = CURRENT_DATE
                    WHERE id_produto = %s AND id_fornecedor = %s
                """, [nova_quantidade, produto_id, supplier_id])
            
            messages.success(request, "Produto e stock atualizados com sucesso!")
            return redirect('supplier_produto_list')
            
        except Exception as e:
            messages.error(request, f"Erro ao atualizar produto: {str(e)}")
    
    categorias = produto_service.get_categorias()
    
    return render(request, 'fornecedor/produto_form.html', {
        'produto': produto, 
        'categorias': categorias,
        'stock_atual': stock_atual,
        'is_edit': True 
    })

def produto_delete(request, produto_id):
    try:
        produto_id = int(produto_id)
    except (ValueError, TypeError):
        messages.error(request, "ID do produto inválido.")
        return redirect('supplier_produto_list')
    produto = produto_service.get_produto(produto_id)
    if request.method == 'POST':
        produto_service.delete_produto(produto_id)
        return redirect('home')
    return render(request, 'produto_confirm_delete.html', {'produto': produto})


def produto_detail(request, produto_id):
    try:
        produto_id_int = int(produto_id)
        produto = produto_service.get_produto(produto_id_int)
    except (ValueError, TypeError):
        produto = produto_service.get_produto(produto_id)
    
    if not produto:
        messages.error(request, "Produto não encontrado.")
        return redirect("home")
    
    # Get supplier name from the stock table (which links product to supplier)
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT u.nome 
                FROM usuario u
                JOIN stock s ON u.id_usuario = s.id_fornecedor
                WHERE s.id_produto = %s
                LIMIT 1
            """, [produto["_id"]])
            supplier_result = cursor.fetchone()
            if supplier_result:
                produto["fornecedor_nome"] = supplier_result[0]
    except Exception as e:
        print(f"Error fetching supplier name: {e}")
    
    # Get reviews from MongoDB
    avaliacoes = produto_service.list_avaliacoes(produto_id=produto["_id"])
    
    if avaliacoes:
        # Get all unique user IDs
        user_ids = list(set(avaliacao["usuario_id"] for avaliacao in avaliacoes))
        
        # Fetch all user names in a single query
        user_names = {}
        try:
            with connection.cursor() as cursor:
                # Use IN clause to fetch all users at once
                placeholders = ','.join(['%s'] * len(user_ids))
                cursor.execute(f"SELECT id_usuario, nome FROM usuario WHERE id_usuario IN ({placeholders})", user_ids)
                for user_id, nome in cursor.fetchall():
                    user_names[user_id] = nome
        except Exception as e:
            print(f"Error fetching user names: {e}")
        
        # Add user names to reviews
        for avaliacao in avaliacoes:
            avaliacao["usuario_nome"] = user_names.get(
                avaliacao["usuario_id"], 
                f"Utilizador #{avaliacao['usuario_id']}"
            )
    
    return render(request, "produto_detail.html", {
        "produto": produto,
        "avaliacoes": avaliacoes
    })

def add_produto(request, produto_id):
    cliente_id = request.session.get("user_id")
    if not cliente_id:
        messages.error(request, "Faça login para adicionar produtos.")
        return redirect("login")

    try:
        with connection.cursor() as cur:
            cur.execute("CALL adicionar_produto_pedido(%s, %s, %s)", [cliente_id, int(produto_id), 1])
        messages.success(request, "Produto adicionado ao pedido.")
    except Exception as e:
        print("Worked")
        messages.error(request, f"Erro ao adicionar produto: {e}")

    return redirect("home")

def submit_avaliacao(request, produto_id):
    if not request.session.get("user_id"):
        messages.error(request, "Precisa de fazer login para avaliar produtos.")
        return redirect("login")
    
    if request.method == "POST":
        try:
            avaliacao_data = {
                "usuario_id": request.session["user_id"],
                "produto_id": int(produto_id),
                "nota": int(request.POST.get("nota")),
                "comentario": request.POST.get("comentario", ""),
                "data": datetime.now()
            }
            
            produto_service.create_avaliacao(avaliacao_data)
            messages.success(request, "Avaliação submetida com sucesso!")
        except Exception as e:
            messages.error(request, f"Erro ao submeter avaliação: {str(e)}")
    
    return redirect("produto_detail", produto_id=produto_id)

# Add these views to your views.py

def supplier_produto_list(request):
    supplier_id = request.session.get("user_id")
    if not supplier_id or request.session.get("tipo_usuario") != "fornecedor":
        messages.error(request, "Acesso negado. Apenas fornecedores podem acessar esta página.")
        return redirect("login")
    
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT DISTINCT s.id_produto 
            FROM stock s 
            WHERE s.id_fornecedor = %s
        """, [supplier_id])
        produto_ids = [row[0] for row in cursor.fetchall()]
    
    produtos = []
    for produto_id in produto_ids:
        produto = produto_service.get_produto(produto_id)
        if produto:
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT quantidade, ultimo_update 
                    FROM stock 
                    WHERE id_produto = %s AND id_fornecedor = %s
                """, [produto_id, supplier_id])
                stock_info = cursor.fetchone()
                if stock_info:
                    produto["stock_quantidade"] = stock_info[0]
                    produto["stock_update"] = stock_info[1]
            produtos.append(produto)
    
    return render(request, 'fornecedor/produto_list.html', {'produtos': produtos})

def supplier_pedidos(request):
    
    supplier_id = request.session.get("user_id")
    if not supplier_id or request.session.get("tipo_usuario") != "fornecedor":
        messages.error(request, "Acesso negado.")
        return redirect("login")
    
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT p.id_pedido, p.status, p.data_efetuado, p.id_cliente,
                   t.id_produto, t.quantidade, u.nome as cliente_nome
            FROM pedido p
            JOIN tem2 t ON p.id_pedido = t.id_pedido
            JOIN stock s ON t.id_produto = s.id_produto
            JOIN usuario u ON p.id_cliente = u.id_usuario
            WHERE s.id_fornecedor = %s
            ORDER BY p.data_efetuado DESC
        """, [supplier_id])
        rows = cursor.fetchall()
    
    pedidos_dict = defaultdict(list)
    pedidos_info = {}
    
    for row in rows:
        id_pedido, status, data_efetuado, id_cliente, id_produto, quantidade, cliente_nome = row
        pedidos_info[id_pedido] = {
            "status": status,
            "data_efetuado": data_efetuado,
            "cliente_nome": cliente_nome
        }
        
        try:
            produto = produto_service.get_produto(id_produto)
            nome_produto = produto.get("nome", f"Produto #{id_produto}")
        except:
            nome_produto = f"Produto #{id_produto}"
        
        pedidos_dict[id_pedido].append({
            "id_produto": id_produto,
            "nome_produto": nome_produto,
            "quantidade": quantidade
        })
        
    pedidos = []
    for id_pedido, produtos in pedidos_dict.items():
        pedidos.append({
            "id_pedido": id_pedido,
            "status": pedidos_info[id_pedido]["status"],
            "data_efetuado": pedidos_info[id_pedido]["data_efetuado"],
            "cliente_nome": pedidos_info[id_pedido]["cliente_nome"],
            "produtos": produtos
        })
    
    return render(request, "fornecedor/pedido_fornecedor.html", {"pedidos": pedidos})

def supplier_promocoes(request):
    supplier_id = request.session.get("user_id")
    if not supplier_id or request.session.get("tipo_usuario") != "fornecedor":
        messages.error(request, "Acesso negado.")
        return redirect("login")
    
    # Get supplier's product IDs
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT DISTINCT id_produto FROM stock WHERE id_fornecedor = %s
        """, [supplier_id])
        produto_ids = [row[0] for row in cursor.fetchall()]
    
    # Get promotions for these products
    promocoes = produto_service.list_promocoes()
    supplier_promocoes = []
    
    for p in promocoes:
        if p["produto_id"] in produto_ids:
            # Check if promotion is active
            agora = datetime.now()
            data_inicio = p.get("data_inicio")
            data_fim = p.get("data_fim")
            
            p["ativa"] = data_inicio <= agora <= data_fim if data_inicio and data_fim else False
            p["futura"] = agora < data_inicio if data_inicio else False
            
            supplier_promocoes.append(p)
    
    # Get product names for dropdown
    produtos = []
    for produto_id in produto_ids:
        produto = produto_service.get_produto(produto_id)
        if produto:
            produtos.append({
                "id": produto_id,
                "nome": produto.get("nome", f"Produto #{produto_id}")
            })
    
    return render(request, "fornecedor/promocao.html", {
        "promocoes": supplier_promocoes,
        "produtos": produtos
    })
    
def promocao_form(request, promocao_id=None):
    supplier_id = request.session.get("user_id")
    if not supplier_id or request.session.get("tipo_usuario") != "fornecedor":
        messages.error(request, "Acesso negado.")
        return redirect("login")
    
    # Get supplier's product IDs for the dropdown
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT DISTINCT id_produto FROM stock WHERE id_fornecedor = %s
        """, [supplier_id])
        produto_ids = [row[0] for row in cursor.fetchall()]
    
    # Get product names for dropdown
    produtos = []
    for produto_id in produto_ids:
        produto = produto_service.get_produto(produto_id)
        if produto:
            produtos.append({
                "id": produto_id,
                "nome": produto.get("nome", f"Produto #{produto_id}")
            })
    
    # Handle form submission
    if request.method == "POST":
        try:
            produto_id = int(request.POST.get("produto"))
            tipo = request.POST.get("tipo")
            valor = float(request.POST.get("valor"))
            data_inicio = datetime.strptime(request.POST.get("data_inicio"), "%Y-%m-%d")
            data_fim = datetime.strptime(request.POST.get("data_fim"), "%Y-%m-%d")
            
            # Validate dates
            if data_inicio >= data_fim:
                messages.error(request, "Data de início deve ser anterior à data de fim.")
                return render(request, "fornecedor/promocao_form.html", {
                    "produtos": produtos,
                    "form_data": request.POST
                })
            
            # Validate product belongs to supplier
            if produto_id not in produto_ids:
                messages.error(request, "Produto não pertence a este fornecedor.")
                return render(request, "fornecedor/promocao_form.html", {
                    "produtos": produtos,
                    "form_data": request.POST
                })
            
            promocao_data = {
                "produto_id": produto_id,
                "tipo": tipo,
                "valor": valor,
                "data_inicio": data_inicio,
                "data_fim": data_fim
            }
            
            if promocao_id:
                # Update existing promotion
                produto_service.update_promocao(promocao_id, promocao_data)
                messages.success(request, "Promoção atualizada com sucesso!")
            else:
                # Create new promotion
                produto_service.create_promocao(promocao_data)
                messages.success(request, "Promoção criada com sucesso!")
            
            return redirect("supplier_promocoes")
            
        except Exception as e:
            messages.error(request, f"Erro ao salvar promoção: {str(e)}")
            return render(request, "fornecedor/promocao_form.html", {
                "produtos": produtos,
                "form_data": request.POST,
                "promocao_id": promocao_id
            })
    
    # Handle GET request
    form_data = {}
    if promocao_id:
        # Editing existing promotion - load data
        promocao = produto_service.get_promocao(promocao_id)
        if promocao:
            form_data = {
                "produto": promocao["produto_id"],
                "tipo": promocao["tipo"],
                "valor": promocao["valor"],
                "data_inicio": promocao["data_inicio"].strftime("%Y-%m-%d") if hasattr(promocao["data_inicio"], 'strftime') else promocao["data_inicio"],
                "data_fim": promocao["data_fim"].strftime("%Y-%m-%d") if hasattr(promocao["data_fim"], 'strftime') else promocao["data_fim"]
            }
    
    return render(request, "fornecedor/promocao_form.html", {
        "produtos": produtos,
        "form_data": form_data,
        "promocao_id": promocao_id
    })
    
def promocao_delete(request, promocao_id):
    supplier_id = request.session.get("user_id")
    if not supplier_id or request.session.get("tipo_usuario") != "fornecedor":
        messages.error(request, "Acesso negado.")
        return redirect("login")
    
    if request.method == "POST":
        try:
            # Verify the promotion belongs to a product from this supplier
            promocao = produto_service.get_promocao(promocao_id)
            if promocao:
                with connection.cursor() as cursor:
                    cursor.execute("""
                        SELECT COUNT(*) FROM stock 
                        WHERE id_produto = %s AND id_fornecedor = %s
                    """, [promocao["produto_id"], supplier_id])
                    
                    if cursor.fetchone()[0] > 0:
                        produto_service.delete_promocao(promocao_id)
                        messages.success(request, "Promoção removida com sucesso!")
                    else:
                        messages.error(request, "Não tem permissão para remover esta promoção.")
            else:
                messages.error(request, "Promoção não encontrada.")
                
        except Exception as e:
            messages.error(request, f"Erro ao remover promoção: {str(e)}")
    
    return redirect("supplier_promocoes")

# Admin views
def admin_dashboard(request):
    """Admin dashboard - only accessible by admin users"""
    user_id = request.session.get("user_id")
    if not user_id:
        return redirect("login")
    
    # Check if user is admin (you might need to add an admin flag to your user table)
    with connection.cursor() as cursor:
        cursor.execute("SELECT tipo_usuario FROM usuario WHERE id_usuario = %s", [user_id])
        user_type = cursor.fetchone()
        if not user_type or user_type[0] != "admin":
            messages.error(request, "Acesso negado. Apenas administradores.")
            return redirect("home")
    
    # Get statistics
    with connection.cursor() as cursor:
        # Count users by type
        cursor.execute("SELECT tipo_usuario, COUNT(*) FROM usuario GROUP BY tipo_usuario")
        user_stats = cursor.fetchall()
        
        # Count total orders
        cursor.execute("SELECT COUNT(*) FROM pedido")
        total_pedidos = cursor.fetchone()[0]
        
        # Count total stock
        cursor.execute("SELECT SUM(quantidade) FROM stock")
        total_stock = cursor.fetchone()[0] or 0
    
    total_produtos = produto_service.produtos_collection.count_documents({})
    
    return render(request, "admin/dashboard.html", {
        "user_stats": user_stats,
        "total_pedidos": total_pedidos,
        "total_stock": total_stock,
        "total_produtos": total_produtos
    })

def admin_users(request):
    """Admin view to manage all users"""
    user_id = request.session.get("user_id")
    if not user_id:
        return redirect("login")
    
    with connection.cursor() as cursor:
        cursor.execute("SELECT tipo_usuario FROM usuario WHERE id_usuario = %s", [user_id])
        user_type = cursor.fetchone()
        if not user_type or user_type[0] != "admin":
            messages.error(request, "Acesso negado.")
            return redirect("home")
        
        # Get all users
        cursor.execute("""
            SELECT u.id_usuario, u.nome, u.email, u.tipo_usuario,
                   c.genero, c.data_nascimento, c.morada,
                   f.nif
            FROM usuario u
            LEFT JOIN cliente c ON u.id_usuario = c.id_cliente
            LEFT JOIN fornecedor f ON u.id_usuario = f.id_fornecedor
            ORDER BY u.tipo_usuario, u.nome
        """)
        users = cursor.fetchall()
    
    return render(request, "admin/users.html", {"users": users})