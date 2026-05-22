from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from decimal import Decimal
from datetime import timedelta
from django.utils import timezone

from .models import Evento, Ingresso, Compra, Categoria, Local


class QRCodeCompraTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username='rafa',
            password='SecurePass123!'
        )

        self.categoria = Categoria.objects.create(nome='Tecnologia')

        self.local = Local.objects.create(
            nome='Lavras Hall',
            endereco='Centro',
            capacidade=500
        )

        self.evento = Evento.objects.create(
            titulo='Evento Teste',
            descricao='Teste',
            local=self.local,
            categoria=self.categoria,
            data_evento=timezone.now() + timedelta(days=10),
            organizador=self.user
        )

        self.ingresso = Ingresso.objects.create(
            evento=self.evento,
            tipo='inteira',
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

        self.assertNotEqual(
            compra1.codigo_uuid,
            compra2.codigo_uuid
        )

    def test_qrcode_gerado(self):
        compra = Compra.objects.create(
            usuario=self.user,
            ingresso=self.ingresso,
            quantidade=1,
            valor_total=50,
            status='confirmada'
        )

        self.assertTrue(compra.qr_code)


class ValidacaoQRTests(TestCase):

    def setUp(self):
        self.organizador = User.objects.create_user(
            username='admin',
            password='SecurePass123!',
            is_staff=True
        )

        self.user = User.objects.create_user(
            username='rafa',
            password='SecurePass123!'
        )

        self.categoria = Categoria.objects.create(nome='Tecnologia')

        self.local = Local.objects.create(
            nome='Lavras Hall',
            endereco='Centro',
            capacidade=500
        )

        self.evento = Evento.objects.create(
            titulo='Evento Teste',
            descricao='Teste',
            local=self.local,
            categoria=self.categoria,
            data_evento=timezone.now() + timedelta(days=10),
            organizador=self.organizador
        )

        self.ingresso = Ingresso.objects.create(
            evento=self.evento,
            tipo='inteira',
            preco=Decimal('50.00'),
            quantidade_disponivel=10
        )

        self.compra = Compra.objects.create(
            usuario=self.user,
            ingresso=self.ingresso,
            quantidade=1,
            valor_total=50,
            status='confirmada'
        )

    def test_validacao_qr_valido(self):
        self.client.login(
            username='admin',
            password='SecurePass123!'
        )

        response = self.client.get(
            reverse('validar_qr', args=[self.compra.codigo_uuid])
        )

        self.compra.refresh_from_db()

        self.assertEqual(self.compra.status, 'presente')

    def test_validacao_qr_invalido(self):
        self.client.login(
            username='admin',
            password='SecurePass123!'
        )

        response = self.client.get(
            '/validar-qr/123e4567-e89b-12d3-a456-426614174000/'
        )

        self.assertEqual(response.status_code, 302)

    def test_qr_ja_utilizado(self):
        self.client.login(
            username='admin',
            password='SecurePass123!'
        )

        self.compra.status = 'presente'
        self.compra.save()

        response = self.client.get(
            reverse('validar_qr', args=[self.compra.codigo_uuid])
        )

        self.compra.refresh_from_db()

        self.assertEqual(self.compra.status, 'presente')