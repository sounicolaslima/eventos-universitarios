from decimal import Decimal
from datetime import timedelta

from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone

from eventos.models import Categoria, Compra, Evento, Ingresso, Local


class IngressoCompraModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testeuser',
            password='123456'
        )

        self.categoria = Categoria.objects.create(
            nome='Palestra'
        )

        self.local = Local.objects.create(
            nome='Auditório Central',
            capacidade=300
        )

        self.evento = Evento.objects.create(
            titulo='Semana Acadêmica',
            descricao='Evento para testar models',
            data_evento=timezone.now() + timedelta(days=10),
            local=self.local,
            categoria=self.categoria,
            preco_base=Decimal('50.00'),
            organizador=self.user
        )

    def test_criacao_ingresso_valido_salva_campos_corretamente(self):
        ingresso = Ingresso.objects.create(
            evento=self.evento,
            tipo='inteira',
            preco=Decimal('75.00'),
            quantidade_disponivel=120
        )

        self.assertIsNotNone(ingresso.id)
        self.assertEqual(ingresso.evento, self.evento)
        self.assertEqual(ingresso.tipo, 'inteira')
        self.assertEqual(ingresso.preco, Decimal('75.00'))
        self.assertEqual(ingresso.quantidade_disponivel, 120)

    def test_criacao_compra_valida_salva_dados_corretamente(self):
        ingresso = Ingresso.objects.create(
            evento=self.evento,
            tipo='vip',
            preco=Decimal('100.00'),
            quantidade_disponivel=50
        )

        compra = Compra.objects.create(
            usuario=self.user,
            ingresso=ingresso,
            quantidade=2,
            valor_total=Decimal('200.00')
        )

        self.assertIsNotNone(compra.id)
        self.assertEqual(compra.usuario, self.user)
        self.assertEqual(compra.ingresso, ingresso)
        self.assertEqual(compra.quantidade, 2)
        self.assertEqual(compra.valor_total, Decimal('200.00'))

    def test_status_padrao_de_compra_recem_criada_e_pendente(self):
        ingresso = Ingresso.objects.create(
            evento=self.evento,
            tipo='meia',
            preco=Decimal('40.00'),
            quantidade_disponivel=80
        )

        compra = Compra.objects.create(
            usuario=self.user,
            ingresso=ingresso,
            quantidade=1,
            valor_total=Decimal('40.00')
        )

        self.assertEqual(compra.status, 'pendente')