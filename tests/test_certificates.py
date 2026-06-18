from datetime import timedelta
from decimal import Decimal
from types import ModuleType
from unittest.mock import patch

from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from django.test import TestCase, override_settings
from django.utils import timezone

from eventos.models import Categoria, Compra, Evento, Ingresso, Local
from eventos.tasks import build_certificate_pdf, generate_certificate, send_confirmation_email


@override_settings(MEDIA_ROOT='/tmp/eventos-universitarios-test-media')
class CertificateTaskTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='participante',
            first_name='Laura',
            last_name='Barboza',
            password='StrongPass123!',
        )
        self.categoria = Categoria.objects.create(nome='Extensão')
        self.local = Local.objects.create(nome='Auditório Central', capacidade=120)
        self.evento = Evento.objects.create(
            titulo='Semana Universitária',
            descricao='Evento acadêmico',
            data_evento=timezone.now() + timedelta(days=1),
            local=self.local,
            categoria=self.categoria,
            preco_base=Decimal('25.00'),
            organizador=self.user,
        )
        self.ingresso = Ingresso.objects.create(
            evento=self.evento,
            tipo='inteira',
            preco=Decimal('25.00'),
            quantidade_disponivel=5,
        )
        self.compra = Compra.objects.create(
            usuario=self.user,
            ingresso=self.ingresso,
            quantidade=1,
            valor_total=Decimal('25.00'),
            status='presente',
        )

    def test_generate_certificate_cria_pdf_para_compra_presente(self):
        result = generate_certificate(self.compra.id)

        self.assertTrue(result)
        self.compra.refresh_from_db()
        self.assertTrue(self.compra.certificado.name.startswith('certificados/'))
        self.assertTrue(self.compra.certificado.name.endswith('.pdf'))
        with self.compra.certificado.open('rb') as certificado:
            self.assertEqual(certificado.read(4), b'%PDF')

    def test_generate_certificate_nao_cria_sem_presenca(self):
        self.compra.status = 'confirmada'
        self.compra.save(update_fields=['status'])

        result = generate_certificate(self.compra.id)

        self.assertFalse(result)
        self.compra.refresh_from_db()
        self.assertFalse(self.compra.certificado)

    def test_generate_certificate_retorna_false_para_compra_inexistente(self):
        self.assertFalse(generate_certificate(999999))

    def test_generate_certificate_nao_regenera_certificado_existente(self):
        self.compra.certificado.save(
            'certificado_existente.pdf',
            ContentFile(b'%PDF-existing'),
            save=True
        )

        result = generate_certificate(self.compra.id)

        self.assertTrue(result)

    def test_build_certificate_pdf_usa_reportlab_quando_disponivel(self):
        reportlab = ModuleType('reportlab')
        reportlab_lib = ModuleType('reportlab.lib')
        reportlab_pagesizes = ModuleType('reportlab.lib.pagesizes')
        reportlab_pagesizes.A4 = (595, 842)
        reportlab_pdfgen = ModuleType('reportlab.pdfgen')
        reportlab_canvas = ModuleType('reportlab.pdfgen.canvas')

        class FakeCanvas:
            def __init__(self, buffer, pagesize):
                self.buffer = buffer

            def setTitle(self, title):
                return None

            def setFont(self, name, size):
                return None

            def drawCentredString(self, x, y, text):
                return None

            def showPage(self):
                return None

            def save(self):
                self.buffer.write(b'%PDF-reportlab')

        reportlab_canvas.Canvas = FakeCanvas
        modules = {
            'reportlab': reportlab,
            'reportlab.lib': reportlab_lib,
            'reportlab.lib.pagesizes': reportlab_pagesizes,
            'reportlab.pdfgen': reportlab_pdfgen,
            'reportlab.pdfgen.canvas': reportlab_canvas,
        }

        with patch.dict('sys.modules', modules):
            self.assertEqual(build_certificate_pdf(self.compra), b'%PDF-reportlab')

    @patch('eventos.tasks.send_mail')
    def test_send_confirmation_email_envia_email(self, send_mail_mock):
        send_confirmation_email(
            'participante@example.com',
            'Semana Universitária',
            1,
            'ABC123'
        )

        send_mail_mock.assert_called_once()
