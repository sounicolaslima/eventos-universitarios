from django.test import TestCase

from unittest.mock import patch

@patch('eventos.tasks.send_mail')
def test_send_confirmation_email(mock_send):
    from eventos.tasks import send_confirmation_email

    send_confirmation_email(
        'teste@email.com',
        'Evento Teste',
        2,
        123
    )

    mock_send.assert_called_once()
