from decimal import Decimal
import itertools
from datetime import timedelta

from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from eventos.models import Categoria, Compra, Evento, Ingresso, Local


class UsuariosViewsTest(TestCase):
    purchase_counter = itertools.count(1)

    def setUp(self):
        self.client = Client()
        self.user_password = 'StrongPass123!'
        self.user = User.objects.create_user(
            username='aluno',
            email='aluno@example.com',
            password=self.user_password,
        )

    def _create_purchase(self, status='presente', with_certificate=False):
        sequence = next(self.purchase_counter)
        categoria = Categoria.objects.create(nome=f'Palestra {sequence}')
        local = Local.objects.create(nome=f'Auditório {sequence}', capacidade=100)
        evento = Evento.objects.create(
            titulo='Evento Dashboard',
            descricao='Desc',
            data_evento=timezone.now() + timedelta(days=10),
            local=local,
            categoria=categoria,
            preco_base=Decimal('10.00'),
            organizador=self.user,
        )
        ingresso = Ingresso.objects.create(
            evento=evento,
            tipo='inteira',
            preco=Decimal('10.00'),
            quantidade_disponivel=10,
        )
        compra = Compra.objects.create(
            usuario=self.user,
            ingresso=ingresso,
            quantidade=1,
            valor_total=Decimal('10.00'),
            status=status,
        )
        if with_certificate:
            compra.certificado = 'certificados/teste.pdf'
            compra.save(update_fields=['certificado'])
        return compra

    def test_registro_get_renderiza_formulario(self):
        response = self.client.get(reverse('registro'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Criar Conta')

    def test_registro_post_cria_usuario_e_redireciona_dashboard(self):
        response = self.client.post(
            reverse('registro'),
            {
                'username': 'novo',
                'email': 'novo@example.com',
                'password1': 'StrongPass123!',
                'password2': 'StrongPass123!',
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('dashboard'))
        self.assertTrue(User.objects.filter(username='novo').exists())

    def test_registro_post_invalido_mostra_formulario(self):
        response = self.client.post(
            reverse('registro'),
            {
                'username': 'novo-invalido',
                'email': 'novo@example.com',
                'password1': '123',
                'password2': '321',
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Erro no cadastro. Verifique os dados.')

    def test_login_get_renderiza_formulario(self):
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Login')

    def test_login_post_valido_redireciona_dashboard(self):
        response = self.client.post(
            reverse('login'),
            {'username': self.user.username, 'password': self.user_password},
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('dashboard'))

    def test_login_post_invalido_retorna_mesma_tela(self):
        response = self.client.post(
            reverse('login'),
            {'username': self.user.username, 'password': 'errada'},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Usuário ou senha inválidos')

    def test_logout_redireciona_home(self):
        self.client.login(username=self.user.username, password=self.user_password)
        response = self.client.get(reverse('logout'))

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('home'))

    def test_dashboard_redireciona_anonimo(self):
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('login'))

    def test_dashboard_mostra_contadores_e_compras(self):
        self._create_purchase(status='presente', with_certificate=True)
        self._create_purchase(status='cancelada', with_certificate=False)
        self.client.login(username=self.user.username, password=self.user_password)

        response = self.client.get(reverse('dashboard'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Ingressos Comprados')
        self.assertContains(response, 'Eventos Participados')
        self.assertContains(response, 'Certificados Obtidos')
        self.assertContains(response, 'Últimas Compras')
        self.assertContains(response, 'Evento Dashboard')