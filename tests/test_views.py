from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from decimal import Decimal
from datetime import timedelta
from eventos.models import Evento, Categoria, Local, Ingresso, Compra
from django.utils import timezone


class EventosViewsTest(TestCase):

    def setUp(self):
        self.client = Client()

        # Usuário
        self.user = User.objects.create_user(
            username='teste',
            password='123456'
        )

        # Categoria e Local (OBRIGATÓRIOS no seu model)
        self.categoria = Categoria.objects.create(
            nome='Categoria Teste'
        )

        self.local = Local.objects.create(
            nome='Local Teste',
            capacidade=100
        )

        # Evento (ajustado ao seu model real)
        self.evento = Evento.objects.create(
            titulo='Evento Teste',
            descricao='Descrição teste',
            data_evento=timezone.now() + timedelta(days=10),
            local=self.local,
            categoria=self.categoria,
            preco_base=10.00,
            organizador=self.user
        )

        self.ingresso = Ingresso.objects.create(
            evento=self.evento,
            tipo='inteira',
            preco=Decimal('50.00'),
            quantidade_disponivel=10
        )

    def login_user(self):
        self.client.login(username='teste', password='123456')

    def test_lista_eventos(self):
        """GET /eventos/ deve retornar 200 e conter eventos"""
        response = self.client.get('/eventos/')

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Evento Teste')

    def test_detalhe_evento(self):
        """GET detalhe deve retornar 200 e conter info"""
        url = f'/evento/{self.evento.id}/'
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Evento Teste')

    def test_view_protegida_redireciona(self):
        """Usuário não autenticado deve ser redirecionado"""
        response = self.client.get('/meu-historico/')

        self.assertEqual(response.status_code, 302)
        self.assertIn('/login', response.url)

    def test_comprar_ingresso_get(self):
        self.login_user()

        response = self.client.get(reverse('comprar_ingresso', args=[self.ingresso.id]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Comprar Ingresso')

    def test_comprar_ingresso_post_redireciona_para_revisao(self):
        self.login_user()

        response = self.client.post(
            reverse('comprar_ingresso', args=[self.ingresso.id]),
            {'quantidade': '2'}
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Revisar compra')
        self.assertContains(response, 'Confirmar compra')

    def test_comprar_ingresso_quantidade_invalida(self):
        self.login_user()

        response = self.client.post(
            reverse('comprar_ingresso', args=[self.ingresso.id]),
            {'quantidade': 'abc'}
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Informe uma quantidade válida.')

    def test_confirmar_compra_cria_compra_e_reduz_estoque(self):
        self.login_user()

        response = self.client.post(
            reverse('confirmar_compra', args=[self.ingresso.id]),
            {'quantidade': '2'}
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Compra simulada confirmada com sucesso!')

        compra = Compra.objects.get(usuario=self.user, ingresso=self.ingresso)
        self.assertEqual(compra.quantidade, 2)
        self.ingresso.refresh_from_db()
        self.assertEqual(self.ingresso.quantidade_disponivel, 8)

    def test_comprar_ingresso_evento_encerrado_redireciona(self):
        self.login_user()

        evento_passado = Evento.objects.create(
            titulo='Evento Passado',
            descricao='Passado',
            data_evento=timezone.now() - timedelta(days=1),
            local=self.local,
            categoria=self.categoria,
            preco_base=10.00,
            organizador=self.user
        )
        ingresso_passado = Ingresso.objects.create(
            evento=evento_passado,
            tipo='inteira',
            preco=Decimal('50.00'),
            quantidade_disponivel=10
        )

        response = self.client.get(reverse('comprar_ingresso', args=[ingresso_passado.id]))

        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('detalhe_evento', args=[evento_passado.id]), response.url)