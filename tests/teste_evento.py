from decimal import Decimal
from datetime import timedelta

from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone

from eventos.models import Categoria, Evento, Local


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
