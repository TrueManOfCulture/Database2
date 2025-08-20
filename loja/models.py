from django.db import models

class Usuario(models.Model):
    ID_USUARIO = models.AutoField(primary_key=True)  # SERIAL in PostgreSQL
    NOME = models.CharField(max_length=255)  # Matching PostgreSQL schema
    EMAIL = models.EmailField(max_length=255, unique=True)  # UNIQUE constraint
    PASSWORD = models.CharField(max_length=255)
    TIPO_USUARIO = models.CharField(max_length=20)  # VARCHAR(20) in schema

    class Meta:
        db_table = 'usuario'  # Lowercase table name in PostgreSQL

    def __str__(self):
        return self.NOME

class Cliente(models.Model):
    ID_CLIENTE = models.OneToOneField(
        Usuario, 
        on_delete=models.CASCADE, 
        primary_key=True,
        db_column='id_cliente'  # Foreign key to Usuario
    )
    GENERO = models.CharField(max_length=20, blank=True, null=True)
    DATA_NASCIMENTO = models.DateField(blank=True, null=True)
    MORADA = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        db_table = 'cliente'

    def __str__(self):
        return f"Cliente: {self.ID_CLIENTE.NOME}"

class Fornecedor(models.Model):
    ID_FORNECEDOR = models.OneToOneField(
        Usuario, 
        on_delete=models.CASCADE, 
        primary_key=True,
        db_column='id_fornecedor'  # Foreign key to Usuario
    )
    NIF = models.CharField(max_length=20, blank=True, null=True)

    class Meta:
        db_table = 'fornecedor'

    def __str__(self):
        return f"Fornecedor: {self.ID_FORNECEDOR.NOME}"

class Pedido(models.Model):
    ID_PEDIDO = models.AutoField(primary_key=True)  # SERIAL in PostgreSQL
    ID_CLIENTE = models.ForeignKey(
        Cliente, 
        on_delete=models.CASCADE, 
        db_column='id_cliente'
    )
    DATA_EFETUADO = models.DateField(auto_now_add=True)  # DEFAULT CURRENT_DATE
    STATUS = models.CharField(max_length=50, default='Pendente')
    DATA_CONCLUIDO = models.DateField(blank=True, null=True)

    class Meta:
        db_table = 'pedido'

    def __str__(self):
        return f"Pedido {self.ID_PEDIDO} - {self.STATUS}"

class Stock(models.Model):
    ID_STOCK = models.AutoField(primary_key=True)  # SERIAL in PostgreSQL
    ID_FORNECEDOR = models.ForeignKey(
        Fornecedor, 
        on_delete=models.CASCADE,
        db_column='id_fornecedor'
    )
    ID_PRODUTO = models.IntegerField()  # Reference to MongoDB Product
    QUANTIDADE = models.IntegerField()
    ULTIMO_UPDATE = models.DateField(auto_now=True)  # DEFAULT CURRENT_DATE

    class Meta:
        db_table = 'stock'

    def __str__(self):
        return f"Stock {self.ID_STOCK} - Produto {self.ID_PRODUTO} ({self.QUANTIDADE})"

class Tem2(models.Model):
    # Composite primary key (ID_PEDIDO, ID_PRODUTO)
    ID_PEDIDO = models.ForeignKey(
        Pedido, 
        on_delete=models.CASCADE,
        db_column='id_pedido'
    )
    ID_PRODUTO = models.IntegerField()  # Reference to MongoDB Product
    QUANTIDADE = models.IntegerField()

    class Meta:
        db_table = 'tem2'
        # Composite primary key
        unique_together = ('ID_PEDIDO', 'ID_PRODUTO')

    def __str__(self):
        return f"Pedido {self.ID_PEDIDO.ID_PEDIDO} - Produto {self.ID_PRODUTO} ({self.QUANTIDADE})"

# Note: Produto and Promocao models removed since they're not in your PostgreSQL schema
# (assuming they're stored in MongoDB as indicated by the comments)

# If you need a Produto model for Django admin or other purposes, 
# you can create an unmanaged model:
class Produto(models.Model):
    # This is an unmanaged model representing MongoDB data
    ID_PRODUTO = models.IntegerField(primary_key=True)
    nome = models.CharField(max_length=255, blank=True, null=True)
    descricao = models.TextField(blank=True, null=True)
    preco = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    categoria = models.CharField(max_length=255, blank=True, null=True)
    marca = models.CharField(max_length=255, blank=True, null=True)
    condicao = models.CharField(max_length=255, blank=True, null=True)
    detalhes_condicao = models.TextField(blank=True, null=True)

    class Meta:
        managed = False  # Django won't manage this table
        db_table = 'produto_virtual'  # Virtual table name

    def __str__(self):
        return self.nome or f"Produto {self.ID_PRODUTO}"

