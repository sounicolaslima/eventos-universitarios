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

    def post_purchase(self, ingresso_id, quantidade):
        self.login_user()
        return self.client.post(
            reverse('comprar_ingresso', args=[ingresso_id]),
            {'quantidade': quantidade}
        )

    def create_past_event_ticket(self):
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
        return evento_passado, ingresso_passado

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
        response = self.post_purchase(self.ingresso.id, '2')

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Revisar compra')
        self.assertContains(response, 'Confirmar compra')

    def test_comprar_ingresso_quantidade_invalida(self):
        response = self.post_purchase(self.ingresso.id, 'abc')

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Informe uma quantidade válida.')

    def test_comprar_ingresso_quantidade_acima_do_estoque(self):
        response = self.post_purchase(self.ingresso.id, '99')

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Quantidade indisponível para este ingresso.')

    def test_confirmar_compra_cria_compra_e_reduz_estoque(self):
        self.login_user()

        response = self.client.post(
            reverse('confirmar_compra', args=[self.ingresso.id]),
            {'quantidade': '2'}
        )

        self.assertEqual(response.status_code, 302)

        compra = Compra.objects.get(usuario=self.user, ingresso=self.ingresso)
        self.assertIn(
            reverse('confirmacao_compra', args=[compra.codigo_uuid]),
            response.url
        )
        self.assertEqual(compra.quantidade, 2)
        self.ingresso.refresh_from_db()
        self.assertEqual(self.ingresso.quantidade_disponivel, 8)

    def test_confirmacao_compra_exibe_dados_da_compra(self):
        self.login_user()
        compra = Compra.objects.create(
            usuario=self.user,
            ingresso=self.ingresso,
            quantidade=2,
            valor_total=Decimal('100.00'),
            status='confirmada'
        )

        response = self.client.get(
            reverse('confirmacao_compra', args=[compra.codigo_uuid])
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, str(compra.codigo_uuid))
        self.assertContains(response, 'Evento Teste')
        self.assertContains(response, 'Inteira')
        self.assertContains(response, '2')
        self.assertContains(response, '100,00')

    def test_confirmacao_compra_nao_abre_para_outro_usuario(self):
        outro = User.objects.create_user(
            username='outro',
            password='123456'
        )
        compra = Compra.objects.create(
            usuario=outro,
            ingresso=self.ingresso,
            quantidade=1,
            valor_total=Decimal('50.00'),
            status='confirmada'
        )
        self.login_user()

        response = self.client.get(
            reverse('confirmacao_compra', args=[compra.codigo_uuid])
        )

        self.assertEqual(response.status_code, 404)

    def test_confirmar_compra_get_redireciona(self):
        self.login_user()

        response = self.client.get(reverse('confirmar_compra', args=[self.ingresso.id]))

        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('comprar_ingresso', args=[self.ingresso.id]), response.url)

    def test_confirmar_compra_quantidade_invalida_redireciona(self):
        self.login_user()

        response = self.client.post(
            reverse('confirmar_compra', args=[self.ingresso.id]),
            {'quantidade': 'abc'}
        )

        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('comprar_ingresso', args=[self.ingresso.id]), response.url)

    def test_comprar_ingresso_evento_encerrado_redireciona(self):
        evento_passado, ingresso_passado = self.create_past_event_ticket()
        self.login_user()

        response = self.client.get(reverse('comprar_ingresso', args=[ingresso_passado.id]))

        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('detalhe_evento', args=[evento_passado.id]), response.url)
