from django.test import TestCase
from django.contrib.auth.models import User
from .models import Evento, Ingresso, Compra
from django.utils import timezone
from decimal import Decimal
from datetime import timedelta

class QRCodeCompraTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username='rafa',
            password='123'
        )

        self.evento = Evento.objects.create(
            titulo='Evento Teste',
            descricao='Teste',
            local='Lavras',
            data_evento=timezone.now() + timedelta(days=10)
        )

        self.ingresso = Ingresso.objects.create(
            evento=self.evento,
            tipo='Inteira',
            preco=Decimal('50.00'),
            quantidade_disponivel=10
        )

    def test_compra_gera_uuid_unico(self):
        compra1 = Compra.objects.create(
            usuario=self.user,
            ingresso=self.ingresso,
            quantidade=1,
            valor_total=50,
            status='confirmada'
        )

        compra2 = Compra.objects.create(
            usuario=self.user,
            ingresso=self.ingresso,
            quantidade=1,
            valor_total=50,
            status='confirmada'
        )

        self.assertNotEqual(compra1.codigo_uuid, compra2.codigo_uuid)

    def test_qrcode_gerado(self):
        compra = Compra.objects.create(
            usuario=self.user,
            ingresso=self.ingresso,
            quantidade=1,
            valor_total=50,
            status='confirmada'
        )

        self.assertTrue(compra.qr_code)