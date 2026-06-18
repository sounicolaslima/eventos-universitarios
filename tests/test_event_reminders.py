from datetime import timedelta
from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone

from eventos.models import Categoria, Compra, Evento, Ingresso, Local
from eventos.tasks import schedule_event_reminder, send_event_reminder


class EventReminderTaskTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='participante',
            email='participante@example.com',
            password='StrongPass123!',
        )
        self.categoria = Categoria.objects.create(nome='Tecnologia')
        self.local = Local.objects.create(nome='Auditório', capacidade=100)
        self.evento = Evento.objects.create(
            titulo='Semana Acadêmica',
            descricao='Evento universitário',
            data_evento=timezone.now() + timedelta(days=3),
            local=self.local,
            categoria=self.categoria,
            preco_base=Decimal('30.00'),
            organizador=self.user,
        )
        self.ingresso = Ingresso.objects.create(
            evento=self.evento,
            tipo='inteira',
            preco=Decimal('30.00'),
            quantidade_disponivel=10,
        )
        self.compra = Compra.objects.create(
            usuario=self.user,
            ingresso=self.ingresso,
            quantidade=1,
            valor_total=Decimal('30.00'),
            status='confirmada',
        )

    @patch('eventos.tasks.send_event_reminder.apply_async')
    def test_schedule_event_reminder_agenda_para_24h_antes(self, apply_async_mock):
        schedule_event_reminder(self.compra)

        expected_eta = self.evento.data_evento - timedelta(hours=24)
        apply_async_mock.assert_called_once_with(
            args=[self.compra.id],
            eta=expected_eta
        )

    @patch('eventos.tasks.send_event_reminder.apply_async')
    def test_schedule_event_reminder_nao_agenda_evento_muito_proximo(self, apply_async_mock):
        self.evento.data_evento = timezone.now() + timedelta(hours=2)
        self.evento.save(update_fields=['data_evento'])

        result = schedule_event_reminder(self.compra)

        self.assertIsNone(result)
        apply_async_mock.assert_not_called()

    @patch('eventos.tasks.send_mail')
    def test_send_event_reminder_envia_email_para_compra_confirmada(self, send_mail_mock):
        result = send_event_reminder(self.compra.id)

        self.assertTrue(result)
        send_mail_mock.assert_called_once()
        self.assertEqual(
            send_mail_mock.call_args.kwargs['recipient_list'],
            ['participante@example.com']
        )

    @patch('eventos.tasks.send_mail')
    def test_send_event_reminder_nao_envia_compra_cancelada(self, send_mail_mock):
        self.compra.status = 'cancelada'
        self.compra.save(update_fields=['status'])

        result = send_event_reminder(self.compra.id)

        self.assertFalse(result)
        send_mail_mock.assert_not_called()
