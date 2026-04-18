from django.db import models
from django.contrib.auth.models import User

class Categoria(models.Model):
    nome = models.CharField(max_length=100, unique=True)
    descricao = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.nome

class Local(models.Model):
    nome = models.CharField(max_length=200)
    endereco = models.CharField(max_length=255)
    capacidade = models.PositiveIntegerField()

    def __str__(self):
        return self.nome

class Evento(models.Model):
    titulo = models.CharField(max_length=200)
    descricao = models.TextField()
    data_evento = models.DateTimeField()
    local = models.ForeignKey(Local, on_delete=models.PROTECT)
    categoria = models.ForeignKey(Categoria, on_delete=models.PROTECT)
    preco_base = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)
    imagem = models.ImageField(upload_to='eventos/', null=True, blank=True)
    organizador = models.ForeignKey(User, on_delete=models.CASCADE)
    data_criacao = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.titulo

class Ingresso(models.Model):
    evento = models.ForeignKey(Evento, on_delete=models.CASCADE)
    tipo = models.CharField(max_length=50, choices=[
        ('inteira', 'Inteira'),
        ('meia', 'Meia entrada'),
        ('vip', 'VIP'),
    ])
    preco = models.DecimalField(max_digits=8, decimal_places=2)
    quantidade_disponivel = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.tipo} - {self.evento.titulo}"

class Compra(models.Model):
    STATUS_CHOICES = [
        ('pendente', 'Pendente'),
        ('paga', 'Paga'),
        ('cancelada', 'Cancelada'),
    ]

    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    ingresso = models.ForeignKey(Ingresso, on_delete=models.CASCADE)
    quantidade = models.PositiveIntegerField(default=1)
    valor_total = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pendente')
    data_compra = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Compra {self.id} de {self.usuario.username} - Status: {self.status}"