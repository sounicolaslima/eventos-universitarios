from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from eventos.models import Evento, Categoria, Local
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
            data_evento=timezone.now(),
            local=self.local,
            categoria=self.categoria,
            preco_base=10.00,
            organizador=self.user
        )

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