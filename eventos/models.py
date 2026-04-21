from django.db import models
from django.contrib.auth.models import User
from decimal import Decimal
import qrcode
from io import BytesIO
from django.core.files import File

class Categoria(models.Model):
    nome = models.CharField(max_length=100, unique=True)
    descricao = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.nome
    
    class Meta:
        verbose_name = 'Categoria'
        verbose_name_plural = 'Categorias'
        ordering = ['nome']


class Local(models.Model):
    nome = models.CharField(max_length=200)
    endereco = models.CharField(max_length=255, blank=True, null=True)
    capacidade = models.PositiveIntegerField(default=100)

    def __str__(self):
        return self.nome
    
    class Meta:
        verbose_name = 'Local'
        verbose_name_plural = 'Locais'
        ordering = ['nome']
    
    @classmethod
    def get_or_create_local(cls, nome, endereco='', capacidade=100):
        """Obtém ou cria um local pelo nome"""
        local, created = cls.objects.get_or_create(
            nome=nome,
            defaults={'endereco': endereco, 'capacidade': capacidade}
        )
        return local, created


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
    
    class Meta:
        verbose_name = 'Evento'
        verbose_name_plural = 'Eventos'
        ordering = ['-data_evento']

    def ingressos_disponiveis(self):
        total = self.ingresso_set.aggregate(total=models.Sum('quantidade_disponivel'))['total']
        return total or 0
    
    def ingressos_vendidos(self):
        from .models import Compra
        from django.db.models import Sum
        total = Compra.objects.filter(
            ingresso__evento=self,
            status__in=['confirmada', 'presente']
        ).aggregate(total=Sum('quantidade'))['total'] or 0
        return total
    
    def receita_total(self):
        from .models import Compra
        from django.db.models import Sum
        total = Compra.objects.filter(
            ingresso__evento=self,
            status__in=['confirmada', 'presente']
        ).aggregate(total=Sum('valor_total'))['total'] or 0
        return total


class Ingresso(models.Model):
    TIPO_CHOICES = [
        ('inteira', 'Inteira'),
        ('meia', 'Meia-entrada'),
        ('vip', 'VIP'),
    ]
    evento = models.ForeignKey(Evento, on_delete=models.CASCADE)
    tipo = models.CharField(max_length=50, choices=TIPO_CHOICES)
    preco = models.DecimalField(max_digits=8, decimal_places=2)
    quantidade_disponivel = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.get_tipo_display()} - {self.evento.titulo}"
    
    class Meta:
        verbose_name = 'Ingresso'
        verbose_name_plural = 'Ingressos'
        ordering = ['evento__data_evento', 'tipo']
    
    def quantidade_vendida(self):
        from .models import Compra
        from django.db.models import Sum
        total = Compra.objects.filter(
            ingresso=self,
            status__in=['confirmada', 'presente']
        ).aggregate(total=Sum('quantidade'))['total'] or 0
        return total


class Compra(models.Model):
    STATUS_CHOICES = [
        ('pendente', 'Pendente'),
        ('confirmada', 'Confirmada'),
        ('cancelada', 'Cancelada'),
        ('presente', 'Presente'),
    ]
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    ingresso = models.ForeignKey(Ingresso, on_delete=models.CASCADE)
    quantidade = models.PositiveIntegerField(default=1)
    valor_total = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pendente')
    data_compra = models.DateTimeField(auto_now_add=True)
    qr_code = models.ImageField(upload_to='qrcodes/', blank=True, null=True)
    certificado = models.FileField(upload_to='certificados/', blank=True, null=True)

    def save(self, *args, **kwargs):
        if not self.qr_code and self.id:
            qr = qrcode.QRCode(version=1, box_size=10, border=5)
            qr.add_data(f'compra_{self.id}_{self.usuario.id}')
            qr.make(fit=True)
            img = qr.make_image(fill='black', back_color='white')
            buffer = BytesIO()
            img.save(buffer, 'PNG')
            self.qr_code.save(f'qr_{self.id}.png', File(buffer), save=False)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Compra {self.id} de {self.usuario.username} - Status: {self.status}"
    
    class Meta:
        verbose_name = 'Compra'
        verbose_name_plural = 'Compras'
        ordering = ['-data_compra']