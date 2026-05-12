from celery import shared_task
from django.core.mail import send_mail

@shared_task
def send_confirmation_email(email, evento, quantidade, codigo):
    print("EMAIL ENVIADO COM SUCESSO")

    send_mail(
        subject='Confirmação de Compra',
        message=f'''
Compra confirmada!

Evento: {evento}
Quantidade: {quantidade}
Código da compra: {codigo}
''',
        from_email=None,
        recipient_list=[email],
        fail_silently=True
    )