from datetime import timedelta
from decimal import Decimal

from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from eventos.models import Categoria, Compra, Evento, Ingresso, Local


@override_settings(MEDIA_ROOT='/tmp/eventos-universitarios-test-media')
class CertificateDownloadTest(TestCase):
    def setUp(self):
        self.password = 'StrongPass123!'
        self.user = User.objects.create_user(
            username='participante',
            password=self.password,
        )
        self.outro_usuario = User.objects.create_user(
            username='outro',
            password=self.password,
        )
        self.categoria = Categoria.objects.create(nome='Tecnologia')
        self.local = Local.objects.create(nome='Auditório', capacidade=100)
        self.evento = Evento.objects.create(
            titulo='Evento com Certificado',
            descricao='Evento',
            data_evento=timezone.now() + timedelta(days=1),
            local=self.local,
            categoria=self.categoria,
            preco_base=Decimal('20.00'),
            organizador=self.user,
        )
        self.ingresso = Ingresso.objects.create(
            evento=self.evento,
            tipo='inteira',
            preco=Decimal('20.00'),
            quantidade_disponivel=5,
        )
        self.compra = Compra.objects.create(
            usuario=self.user,
            ingresso=self.ingresso,
            quantidade=1,
            valor_total=Decimal('20.00'),
            status='presente',
        )
        self.compra.certificado.save(
            'certificado.pdf',
            ContentFile(b'%PDF-1.4 certificado'),
            save=True
        )

    def test_historico_exibe_link_de_download_do_certificado(self):
        self.client.login(username='participante', password=self.password)

        response = self.client.get(reverse('meu_historico'))

        self.assertContains(response, reverse('download_certificado', args=[self.compra.id]))
        self.assertContains(response, 'Baixar Certificado')

    def test_download_certificado_autorizado(self):
        self.client.login(username='participante', password=self.password)

        response = self.client.get(reverse('download_certificado', args=[self.compra.id]))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')
        self.assertIn('attachment;', response['Content-Disposition'])
        self.assertEqual(b''.join(response.streaming_content), b'%PDF-1.4 certificado')

    def test_download_certificado_nao_abre_para_outro_usuario(self):
        self.client.login(username='outro', password=self.password)

        response = self.client.get(reverse('download_certificado', args=[self.compra.id]))

        self.assertEqual(response.status_code, 404)

    def test_download_certificado_exige_presenca_confirmada(self):
        self.compra.status = 'confirmada'
        self.compra.save(update_fields=['status'])
        self.client.login(username='participante', password=self.password)

        response = self.client.get(reverse('download_certificado', args=[self.compra.id]))

        self.assertEqual(response.status_code, 404)

    def test_download_certificado_retorna_404_sem_arquivo(self):
        self.compra.certificado.delete(save=True)
        self.client.login(username='participante', password=self.password)

        response = self.client.get(reverse('download_certificado', args=[self.compra.id]))

        self.assertEqual(response.status_code, 404)
