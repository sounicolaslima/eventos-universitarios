from celery import shared_task
from django.core.mail import send_mail
from django.utils import timezone

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


@shared_task
def send_event_reminder(compra_id):
    from .models import Compra

    compra = Compra.objects.select_related(
        'usuario',
        'ingresso',
        'ingresso__evento'
    ).filter(id=compra_id).first()

    if not compra or compra.status == 'cancelada':
        return False

    evento = compra.ingresso.evento

    send_mail(
        subject=f'Lembrete do evento {evento.titulo}',
        message=f'''
Olá, {compra.usuario.username}!

Seu evento acontece em 24 horas.

Evento: {evento.titulo}
Data: {timezone.localtime(evento.data_evento).strftime('%d/%m/%Y %H:%M')}
Quantidade: {compra.quantidade}
Código da compra: {compra.codigo_uuid}
''',
        from_email=None,
        recipient_list=[compra.usuario.email],
        fail_silently=True
    )

    return True


def schedule_event_reminder(compra):
    evento = compra.ingresso.evento
    eta = evento.data_evento - timezone.timedelta(hours=24)

    if eta <= timezone.now():
        return None

    return send_event_reminder.apply_async(args=[compra.id], eta=eta)
