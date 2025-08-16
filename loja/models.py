from django.db import models

class Usuario(models.Model):
    ID_USUARIO = models.IntegerField(primary_key=True)  # Use the exact column name as in your DB
    nome = models.CharField(max_length=1024)
    morada = models.CharField(max_length=1024)
    email = models.EmailField(blank=True, null=True)
    tipo_usuario = models.CharField(max_length=1024)
    password = models.CharField(max_length=1024)

    class Meta:
        db_table = 'usuario'  # Table name as per your schema

    def __str__(self):
        return self.nome

class Produto(models.Model):
    ID_PRODUTO = models.IntegerField(primary_key=True)  # Matching column name in the database
    nome = models.CharField(max_length=1024)
    descricao = models.CharField(max_length=1024, blank=True, null=True)
    preco = models.FloatField()
    categoria = models.CharField(max_length=1024)
    marca = models.CharField(max_length=1024)
    condicao = models.CharField(max_length=1024)
    detalhes_condicao = models.CharField(max_length=1024, blank=True, null=True)

    class Meta:
        db_table = 'produto'  # Table name as per your schema

    def __str__(self):
        return self.nome

class Stock(models.Model):
    ID_STOCK = models.IntegerField(primary_key=True)  # Use the correct primary key
    produto = models.ForeignKey(Produto, on_delete=models.CASCADE, related_name='stocks')  # Correct foreign key relation
    quantidade = models.IntegerField()
    ultimo_update_data = models.DateField(auto_now=True)
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, null=True, blank=True)

    class Meta:
        db_table = 'stock'  # Table name as per your schema

    def __str__(self):
        return f"{self.produto.nome} - {self.quantidade}"

class Pedido(models.Model):
    ID_PEDIDO = models.IntegerField(primary_key=True)  # Use the correct primary key
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='pedidos')
    pedido_data = models.DateField(auto_now_add=True)
    status = models.CharField(max_length=1024)

    class Meta:
        db_table = 'PEDIDO'  # Table name as per your schema

    def __str__(self):
        return f"Pedido {self.ID_PEDIDO} - {self.status}"

class Promocao(models.Model):
    ID_PROMOCAO = models.IntegerField(primary_key=True)  # Use the correct primary key
    produto = models.ForeignKey(Produto, on_delete=models.CASCADE, related_name='promocoes')
    tipo = models.CharField(max_length=1024)
    valor = models.FloatField()
    data_inicio = models.DateField()
    data_fim = models.DateField()

    class Meta:
        db_table = 'promocao'  # Table name as per your schema

    def __str__(self):
        return f"Promoção {self.tipo} - {self.produto.nome}"

class PedidoProduto(models.Model):
    ID_PEDIDO_PRODUTO = models.IntegerField(primary_key=True)  # Correct primary key for the linking table
    pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE, related_name='pedido_produtos')
    produto = models.ForeignKey(Produto, on_delete=models.CASCADE, related_name='pedido_produtos')
    quantidade = models.PositiveIntegerField()

    class Meta:
        db_table = 'pedido_produto'  # Table name as per your schema

    def __str__(self):
        return f"Pedido {self.pedido.ID_PEDIDO} - {self.produto.nome} ({self.quantidade})"

