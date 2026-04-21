from decimal import Decimal
from datetime import timedelta

from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone

from eventos.models import Categoria, Compra, Evento, Ingresso, Local


class EventoModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='organizador',
            password='123456'
        )
        self.categoria = Categoria.objects.create(nome='Semana Acadêmica')
        self.local = Local.objects.create(nome='Auditório', capacidade=300)

    def _criar_evento(self, titulo='Evento X', **kwargs):
        defaults = {
            'titulo': titulo,
            'descricao': 'Descrição do evento',
            'data_evento': timezone.now() + timedelta(days=10),
            'local': self.local,
            'categoria': self.categoria,
            'preco_base': Decimal('50.00'),
            'organizador': self.user,
        }
        defaults.update(kwargs)
        return Evento.objects.create(**defaults)

    def test_criacao_evento_valido_salva_campos_corretamente(self):
        evento = self._criar_evento(
            titulo='Hackathon',
            descricao='Maratona de programação',
            preco_base=Decimal('30.00')
        )

        self.assertIsNotNone(evento.id)
        self.assertEqual(evento.titulo, 'Hackathon')
        self.assertEqual(evento.descricao, 'Maratona de programação')
        self.assertEqual(evento.local, self.local)
        self.assertEqual(evento.categoria, self.categoria)
        self.assertEqual(evento.preco_base, Decimal('30.00'))
        self.assertEqual(evento.organizador, self.user)
        self.assertIsNotNone(evento.data_criacao)

    def test_evento_str_retorna_titulo(self):
        evento = self._criar_evento(titulo='Minicurso Django')

        self.assertEqual(str(evento), 'Minicurso Django')

    def test_evento_preco_base_padrao_e_zero(self):
        evento = Evento.objects.create(
            titulo='Evento Gratuito',
            descricao='Sem custo',
            data_evento=timezone.now() + timedelta(days=5),
            local=self.local,
            categoria=self.categoria,
            organizador=self.user,
        )

        self.assertEqual(evento.preco_base, Decimal('0.00'))

    def test_evento_ingressos_disponiveis_zero_sem_ingressos(self):
        evento = self._criar_evento()

        self.assertEqual(evento.ingressos_disponiveis(), 0)

    def test_evento_ingressos_disponiveis_soma_quantidade_de_todos_os_tipos(self):
        evento = self._criar_evento()
        Ingresso.objects.create(
            evento=evento, tipo='inteira',
            preco=Decimal('50.00'), quantidade_disponivel=100
        )
        Ingresso.objects.create(
            evento=evento, tipo='meia',
            preco=Decimal('25.00'), quantidade_disponivel=40
        )
        Ingresso.objects.create(
            evento=evento, tipo='vip',
            preco=Decimal('150.00'), quantidade_disponivel=10
        )

        self.assertEqual(evento.ingressos_disponiveis(), 150)

    def test_evento_ingressos_vendidos_considera_confirmadas_e_presentes(self):
        evento = self._criar_evento()
        ingresso = Ingresso.objects.create(
            evento=evento, tipo='inteira',
            preco=Decimal('50.00'), quantidade_disponivel=100
        )

        Compra.objects.create(
            usuario=self.user, ingresso=ingresso,
            quantidade=2, valor_total=Decimal('100.00'),
            status='confirmada'
        )
        Compra.objects.create(
            usuario=self.user, ingresso=ingresso,
            quantidade=3, valor_total=Decimal('150.00'),
            status='presente'
        )
        Compra.objects.create(
            usuario=self.user, ingresso=ingresso,
            quantidade=5, valor_total=Decimal('250.00'),
            status='pendente'
        )
        Compra.objects.create(
            usuario=self.user, ingresso=ingresso,
            quantidade=4, valor_total=Decimal('200.00'),
            status='cancelada'
        )

        self.assertEqual(evento.ingressos_vendidos(), 5)

    def test_evento_ingressos_vendidos_zero_quando_nao_ha_compras(self):
        evento = self._criar_evento()

        self.assertEqual(evento.ingressos_vendidos(), 0)

    def test_evento_receita_total_soma_apenas_status_validos(self):
        evento = self._criar_evento()
        ingresso = Ingresso.objects.create(
            evento=evento, tipo='inteira',
            preco=Decimal('50.00'), quantidade_disponivel=100
        )

        Compra.objects.create(
            usuario=self.user, ingresso=ingresso,
            quantidade=2, valor_total=Decimal('100.00'),
            status='confirmada'
        )
        Compra.objects.create(
            usuario=self.user, ingresso=ingresso,
            quantidade=1, valor_total=Decimal('50.00'),
            status='presente'
        )
        Compra.objects.create(
            usuario=self.user, ingresso=ingresso,
            quantidade=3, valor_total=Decimal('150.00'),
            status='cancelada'
        )

        self.assertEqual(evento.receita_total(), Decimal('150.00'))

    def test_evento_receita_total_zero_sem_compras(self):
        evento = self._criar_evento()

        self.assertEqual(evento.receita_total(), 0)

    def test_evento_meta_ordering_descendente_por_data(self):
        self._criar_evento(
            titulo='Antigo',
            data_evento=timezone.now() + timedelta(days=1)
        )
        self._criar_evento(
            titulo='Novo',
            data_evento=timezone.now() + timedelta(days=30)
        )
        self._criar_evento(
            titulo='Meio',
            data_evento=timezone.now() + timedelta(days=15)
        )

        titulos = list(Evento.objects.values_list('titulo', flat=True))
        self.assertEqual(titulos, ['Novo', 'Meio', 'Antigo'])
