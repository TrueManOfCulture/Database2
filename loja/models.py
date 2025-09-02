from django.db import models

class Usuario(models.Model):
    id_usuario = models.AutoField(primary_key=True)
    nome = models.CharField(max_length=255, default="Unkno")
    email = models.EmailField(max_length=255, unique=True)
    password = models.CharField(max_length=255)
    tipo_usuario = models.CharField(max_length=20)

    class Meta:
        db_table = 'usuario'
        managed = False

    def __str__(self):
        return self.nome

class Cliente(models.Model):
    id_cliente = models.OneToOneField(
        Usuario, 
        on_delete=models.CASCADE, 
        primary_key=True
    )
    genero = models.CharField(max_length=20, blank=True, null=True)
    data_nascimento = models.DateField(blank=True, null=True)
    morada = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        db_table = 'cliente'
        managed = False

    def __str__(self):
        return f"Cliente: {self.id_cliente.nome}"

class Fornecedor(models.Model):
    id_fornecedor = models.OneToOneField(
        Usuario, 
        on_delete=models.CASCADE, 
        primary_key=True
    )
    nif = models.CharField(max_length=20, blank=True, null=True)

    class Meta:
        db_table = 'fornecedor'
        managed = False

    def __str__(self):
        return f"Fornecedor: {self.id_fornecedor.nome}"

class Pedido(models.Model):
    id_pedido = models.AutoField(primary_key=True)
    id_cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, db_column='id_cliente')
    data_efetuado = models.DateField(auto_now_add=True)
    status = models.CharField(max_length=50, default='Pendente')
    data_concluido = models.DateField(blank=True, null=True)

    class Meta:
        db_table = 'pedido'
        managed = False

    def __str__(self):
        return f"Pedido {self.id_pedido} - {self.status}"

class Stock(models.Model):
    id_stock = models.AutoField(primary_key=True)
    id_fornecedor = models.ForeignKey(Fornecedor, on_delete=models.CASCADE, db_column='id_fornecedor')
    id_produto = models.IntegerField()
    quantidade = models.IntegerField()
    ultimo_update = models.DateField(auto_now=True)

    class Meta:
        db_table = 'stock'
        managed = False

    def __str__(self):
        return f"Stock {self.id_stock} - Produto {self.id_produto} ({self.quantidade})"

class Tem2(models.Model):
    id_pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE, db_column='id_pedido')
    id_produto = models.IntegerField()
    quantidade = models.IntegerField()

    class Meta:
        db_table = 'tem2'
        unique_together = ('id_pedido', 'id_produto')
        managed = False

    def __str__(self):
        return f"Pedido {self.id_pedido.id_pedido} - Produto {self.id_produto} ({self.quantidade})"

class Produto(models.Model):
    id_produto = models.IntegerField(primary_key=True)
    nome = models.CharField(max_length=255, blank=True, null=True)
    descricao = models.TextField(blank=True, null=True)
    preco = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    categoria = models.CharField(max_length=255, blank=True, null=True)
    marca = models.CharField(max_length=255, blank=True, null=True)
    condicao = models.CharField(max_length=255, blank=True, null=True)
    detalhes_condicao = models.TextField(blank=True, null=True)

    class Meta:
        managed = False

    def __str__(self):
        return self.nome or f"Produto {self.id_produto}"