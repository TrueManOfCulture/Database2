from djongo import models
from django.db import models as pg_models
from .models import Produto, Usuario  # Importa os modelos do PostgreSQL

class Avaliacao(models.Model):
    produto = pg_models.ForeignKey(Produto, on_delete=pg_models.CASCADE)
    usuario = pg_models.ForeignKey(Usuario, on_delete=pg_models.CASCADE)
    comentario = models.TextField()
    nota = models.IntegerField()
    data = models.DateTimeField(auto_now_add=True)

    class Meta:
        abstract = False
