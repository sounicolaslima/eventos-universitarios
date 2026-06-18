from decimal import Decimal
from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from eventos.models import Categoria, Compra, Evento, Ingresso, Local


class EventosViewsExtraTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.organizador = User.objects.create_user(
            username='organizador',
            password='StrongPass123!',
            is_staff=True,
        )
        self.outro_usuario = User.objects.create_user(
            username='comprador',
            password='StrongPass123!',
        )
        self.categoria = Categoria.objects.create(nome='Tecnologia')
        self.local = Local.objects.create(nome='Auditório', capacidade=200)
        self.evento = Evento.objects.create(
            titulo='Evento Principal',
            descricao='Descrição',
            data_evento=timezone.now() + timedelta(days=10),
            local=self.local,
            categoria=self.categoria,
            preco_base=Decimal('20.00'),
            organizador=self.organizador,
        )
        self.ingresso = Ingresso.objects.create(
            evento=self.evento,
            tipo='inteira',
            preco=Decimal('20.00'),
            quantidade_disponivel=20,
        )
        self.image = SimpleUploadedFile('evento.png', b'fake-image-bytes', content_type='image/png')

    def login_organizador(self):
        self.client.login(username='organizador', password='StrongPass123!')

    def test_home_renderiza(self):
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)

    def test_lista_eventos_filtra_por_titulo_categoria_e_data(self):
        response = self.client.get(reverse('lista_eventos'), {'q': 'Principal'})
        self.assertContains(response, 'Evento Principal')

        response = self.client.get(reverse('lista_eventos'), {'categoria': self.categoria.id})
        self.assertContains(response, 'Evento Principal')

        data_local = timezone.localtime(self.evento.data_evento).date().isoformat()
        response = self.client.get(reverse('lista_eventos'), {'data': data_local})
        self.assertContains(response, 'Evento Principal')

    def test_detalhe_evento_renderiza_ingressos(self):
        response = self.client.get(reverse('detalhe_evento', args=[self.evento.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Evento Principal')

    def test_meu_historico_exige_login(self):
        response = self.client.get(reverse('meu_historico'))
        self.assertEqual(response.status_code, 302)

    def test_meu_historico_exibe_compras(self):
        Compra.objects.create(
            usuario=self.outro_usuario,
            ingresso=self.ingresso,
            quantidade=1,
            valor_total=Decimal('20.00'),
            status='confirmada',
        )
        self.client.login(username='comprador', password='StrongPass123!')

        response = self.client.get(reverse('meu_historico'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Evento Principal')

    def test_meus_eventos_lista_apenas_eventos_do_organizador(self):
        Evento.objects.create(
            titulo='Outro Evento',
            descricao='Desc',
            data_evento=timezone.now() + timedelta(days=20),
            local=self.local,
            categoria=self.categoria,
            preco_base=Decimal('10.00'),
            organizador=self.outro_usuario,
        )
        self.login_organizador()

        response = self.client.get(reverse('meus_eventos'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Evento Principal')
        self.assertNotContains(response, 'Outro Evento')

    def test_criar_evento_get(self):
        self.login_organizador()
        response = self.client.get(reverse('criar_evento'))
        self.assertEqual(response.status_code, 200)

    def test_criar_evento_post_com_falta_de_campos_redireciona(self):
        self.login_organizador()
        response = self.client.post(reverse('criar_evento'), {'titulo': 'Incompleto'})
        self.assertEqual(response.status_code, 302)

    def test_criar_evento_post_cria_local_e_evento(self):
        self.login_organizador()
        response = self.client.post(
            reverse('criar_evento'),
            {
                'titulo': 'Novo Evento',
                'descricao': 'Desc',
                'data_evento': (timezone.now() + timedelta(days=30)).strftime('%Y-%m-%dT%H:%M'),
                'local_nome': 'Sala Nova',
                'local_endereco': 'Bloco B',
                'categoria': self.categoria.id,
                'preco_base': '15.00',
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Evento.objects.filter(titulo='Novo Evento').exists())

    def test_criar_evento_post_cria_local_com_imagem(self):
        self.login_organizador()
        response = self.client.post(
            reverse('criar_evento'),
            {
                'titulo': 'Novo Evento Imagem',
                'descricao': 'Desc',
                'data_evento': (timezone.now() + timedelta(days=30)).strftime('%Y-%m-%dT%H:%M'),
                'local_nome': 'Sala com imagem',
                'local_endereco': 'Bloco D',
                'categoria': self.categoria.id,
                'preco_base': '15.00',
                'imagem': self.image,
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Evento.objects.filter(titulo='Novo Evento Imagem').exists())

    def test_editar_evento_get(self):
        self.login_organizador()
        response = self.client.get(reverse('editar_evento', args=[self.evento.id]))
        self.assertEqual(response.status_code, 200)

    def test_editar_evento_post_atualiza_evento(self):
        self.login_organizador()
        response = self.client.post(
            reverse('editar_evento', args=[self.evento.id]),
            {
                'titulo': 'Evento Atualizado',
                'descricao': 'Nova desc',
                'data_evento': (timezone.now() + timedelta(days=40)).strftime('%Y-%m-%dT%H:%M'),
                'categoria': self.categoria.id,
                'preco_base': '30.00',
                'local_nome': 'Auditório 2',
                'local_endereco': 'Bloco C',
            },
        )
        self.assertEqual(response.status_code, 302)
        self.evento.refresh_from_db()
        self.assertEqual(self.evento.titulo, 'Evento Atualizado')

    def test_excluir_evento_get(self):
        self.login_organizador()
        response = self.client.get(reverse('excluir_evento', args=[self.evento.id]))
        self.assertEqual(response.status_code, 200)

    def test_excluir_evento_post_remove(self):
        self.login_organizador()
        response = self.client.post(reverse('excluir_evento', args=[self.evento.id]))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Evento.objects.filter(id=self.evento.id).exists())

    def test_adicionar_ingresso_get(self):
        self.login_organizador()
        response = self.client.get(reverse('adicionar_ingresso', args=[self.evento.id]))
        self.assertEqual(response.status_code, 200)

    def test_adicionar_ingresso_post_com_falta_de_campos_redireciona(self):
        self.login_organizador()
        response = self.client.post(reverse('adicionar_ingresso', args=[self.evento.id]), {'tipo': 'inteira'})
        self.assertEqual(response.status_code, 302)

    def test_adicionar_ingresso_post_cria_ingresso(self):
        self.login_organizador()
        response = self.client.post(
            reverse('adicionar_ingresso', args=[self.evento.id]),
            {'tipo': 'vip', 'preco': '99.90', 'quantidade': '5'},
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Ingresso.objects.filter(evento=self.evento, tipo='vip').exists())

    def test_editar_ingresso_get(self):
        self.login_organizador()
        response = self.client.get(reverse('editar_ingresso', args=[self.ingresso.id]))
        self.assertEqual(response.status_code, 200)

    def test_editar_ingresso_post_atualiza(self):
        self.login_organizador()
        response = self.client.post(
            reverse('editar_ingresso', args=[self.ingresso.id]),
            {'tipo': 'meia', 'preco': '15.00', 'quantidade': '10'},
        )
        self.assertEqual(response.status_code, 302)
        self.ingresso.refresh_from_db()
        self.assertEqual(self.ingresso.tipo, 'meia')

    def test_excluir_ingresso_get(self):
        self.login_organizador()
        response = self.client.get(reverse('excluir_ingresso', args=[self.ingresso.id]))
        self.assertEqual(response.status_code, 200)

    def test_excluir_ingresso_post_remove(self):
        self.login_organizador()
        response = self.client.post(reverse('excluir_ingresso', args=[self.ingresso.id]))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Ingresso.objects.filter(id=self.ingresso.id).exists())

    def test_validar_qr_nao_staff_forbidden(self):
        self.client.login(username='comprador', password='StrongPass123!')
        response = self.client.get(reverse('validar_qr', args=['123e4567-e89b-12d3-a456-426614174000']))
        self.assertEqual(response.status_code, 403)

    def test_validar_qr_invalido_redireciona_home(self):
        self.client.login(username='organizador', password='StrongPass123!')
        response = self.client.get(reverse('validar_qr', args=['123e4567-e89b-12d3-a456-426614174000']))
        self.assertEqual(response.status_code, 302)

    @patch('eventos.views.generate_certificate.delay')
    def test_validar_qr_marca_presenca(self, certificate_delay):
        self.client.login(username='organizador', password='StrongPass123!')
        compra = Compra.objects.create(
            usuario=self.outro_usuario,
            ingresso=self.ingresso,
            quantidade=1,
            valor_total=Decimal('20.00'),
            status='confirmada',
        )
        response = self.client.get(reverse('validar_qr', args=[compra.codigo_uuid]))
        self.assertEqual(response.status_code, 302)
        compra.refresh_from_db()
        self.assertEqual(compra.status, 'presente')
        certificate_delay.assert_called_once_with(compra.id)

    def test_validar_qr_ja_utilizado(self):
        self.client.login(username='organizador', password='StrongPass123!')
        compra = Compra.objects.create(
            usuario=self.outro_usuario,
            ingresso=self.ingresso,
            quantidade=1,
            valor_total=Decimal('20.00'),
            status='presente',
        )
        response = self.client.get(reverse('validar_qr', args=[compra.codigo_uuid]))
        self.assertEqual(response.status_code, 302)

    def test_comprar_ingresso_quantidade_minima(self):
        self.client.login(username='comprador', password='StrongPass123!')
        response = self.client.post(
            reverse('comprar_ingresso', args=[self.ingresso.id]),
            {'quantidade': '0'},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'A quantidade mínima para compra é 1 ingresso.')

    def test_confirmar_compra_quantidade_minima_redireciona(self):
        self.login_organizador()

        response = self.client.post(
            reverse('confirmar_compra', args=[self.ingresso.id]),
            {'quantidade': '0'},
        )

        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('comprar_ingresso', args=[self.ingresso.id]), response.url)

    def test_confirmar_compra_evento_encerrado_redireciona(self):
        self.login_organizador()
        evento_passado = Evento.objects.create(
            titulo='Evento Passado',
            descricao='Desc',
            data_evento=timezone.now() - timedelta(days=1),
            local=self.local,
            categoria=self.categoria,
            preco_base=Decimal('10.00'),
            organizador=self.organizador,
        )
        ingresso_passado = Ingresso.objects.create(
            evento=evento_passado,
            tipo='inteira',
            preco=Decimal('10.00'),
            quantidade_disponivel=5,
        )

        response = self.client.post(
            reverse('confirmar_compra', args=[ingresso_passado.id]),
            {'quantidade': '1'},
        )

        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('detalhe_evento', args=[evento_passado.id]), response.url)

    def test_confirmar_compra_sem_estoque_redireciona(self):
        self.login_organizador()
        self.ingresso.quantidade_disponivel = 1
        self.ingresso.save(update_fields=['quantidade_disponivel'])

        response = self.client.post(
            reverse('confirmar_compra', args=[self.ingresso.id]),
            {'quantidade': '2'},
        )

        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('comprar_ingresso', args=[self.ingresso.id]), response.url)

    def test_criar_evento_post_com_imagem(self):
        self.login_organizador()
        response = self.client.post(
            reverse('criar_evento'),
            {
                'titulo': 'Novo Evento Imagem',
                'descricao': 'Desc',
                'data_evento': (timezone.now() + timedelta(days=30)).strftime('%Y-%m-%dT%H:%M'),
                'local_nome': 'Sala com imagem',
                'local_endereco': 'Bloco D',
                'categoria': self.categoria.id,
                'preco_base': '15.00',
                'imagem': self.image,
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Evento.objects.filter(titulo='Novo Evento Imagem').exists())

    def test_editar_evento_post_local_existente_nao_cria_novo(self):
        self.login_organizador()
        response = self.client.post(
            reverse('editar_evento', args=[self.evento.id]),
            {
                'titulo': 'Evento Principal',
                'descricao': 'Descrição nova',
                'data_evento': (timezone.now() + timedelta(days=50)).strftime('%Y-%m-%dT%H:%M'),
                'categoria': self.categoria.id,
                'preco_base': '35.00',
                'local_nome': self.local.nome,
                'local_endereco': self.local.endereco or '',
            },
        )
        self.assertEqual(response.status_code, 302)

    def test_editar_evento_post_com_imagem(self):
        self.login_organizador()
        response = self.client.post(
            reverse('editar_evento', args=[self.evento.id]),
            {
                'titulo': 'Evento com Imagem',
                'descricao': 'Nova desc',
                'data_evento': (timezone.now() + timedelta(days=40)).strftime('%Y-%m-%dT%H:%M'),
                'categoria': self.categoria.id,
                'preco_base': '30.00',
                'local_nome': 'Auditório 2',
                'local_endereco': 'Bloco C',
                'imagem': self.image,
            },
        )
        self.assertEqual(response.status_code, 302)

    def test_editar_evento_post_com_falta_de_campos_redireciona(self):
        self.login_organizador()
        response = self.client.post(
            reverse('editar_evento', args=[self.evento.id]),
            {'titulo': 'Sem resto'}
        )
        self.assertEqual(response.status_code, 302)

    def test_editar_evento_post_com_excecao_redireciona(self):
        self.login_organizador()
        with patch('eventos.views.Evento.save', side_effect=Exception('boom')):
            response = self.client.post(
                reverse('editar_evento', args=[self.evento.id]),
                {
                    'titulo': 'Evento',
                    'descricao': 'Desc',
                    'data_evento': (timezone.now() + timedelta(days=40)).strftime('%Y-%m-%dT%H:%M'),
                    'categoria': self.categoria.id,
                    'preco_base': '30.00',
                    'local_nome': 'Auditório 2',
                    'local_endereco': 'Bloco C',
                },
            )
        self.assertEqual(response.status_code, 302)

    def test_adicionar_ingresso_post_com_valores_invalidos_redireciona(self):
        self.login_organizador()
        response = self.client.post(
            reverse('adicionar_ingresso', args=[self.evento.id]),
            {'tipo': 'inteira', 'preco': 'abc', 'quantidade': 'xyz'},
        )
        self.assertEqual(response.status_code, 302)
