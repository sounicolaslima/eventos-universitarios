from celery import shared_task
from django.core.files.base import ContentFile
from django.core.mail import send_mail
from django.utils import timezone
from io import BytesIO

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


def build_certificate_pdf(compra):
    evento = compra.ingresso.evento
    participante = compra.usuario.get_full_name() or compra.usuario.username
    data_evento = timezone.localtime(evento.data_evento).strftime('%d/%m/%Y')
    linhas = [
        'Certificado de Participação',
        f'Participante: {participante}',
        f'Evento: {evento.titulo}',
        f'Data: {data_evento}',
    ]

    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfgen import canvas
    except ImportError:
        conteudo = '\\n'.join(linhas)
        return (
            b'%PDF-1.4\n'
            b'1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj\n'
            b'2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj\n'
            b'3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] '
            b'/Contents 4 0 R >> endobj\n'
            b'4 0 obj << /Length 140 >> stream\n'
            b'BT /F1 18 Tf 72 760 Td (Certificado de Participacao) Tj '
            + f'0 -40 Td ({conteudo}) Tj'.encode('latin-1', errors='ignore') +
            b' ET\nendstream endobj\n'
            b'trailer << /Root 1 0 R >>\n%%EOF\n'
        )

    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    pdf.setTitle('Certificado de Participação')
    pdf.setFont('Helvetica-Bold', 24)
    pdf.drawCentredString(297, 720, linhas[0])
    pdf.setFont('Helvetica', 14)
    pdf.drawCentredString(297, 640, linhas[1])
    pdf.drawCentredString(297, 610, linhas[2])
    pdf.drawCentredString(297, 580, linhas[3])
    pdf.showPage()
    pdf.save()
    return buffer.getvalue()


@shared_task
def generate_certificate(compra_id):
    from .models import Compra

    compra = Compra.objects.select_related(
        'usuario',
        'ingresso',
        'ingresso__evento'
    ).filter(id=compra_id).first()

    if not compra or compra.status != 'presente':
        return False

    if compra.certificado:
        return True

    pdf_bytes = build_certificate_pdf(compra)
    filename = f'certificado_compra_{compra.id}.pdf'
    compra.certificado.save(
        filename,
        ContentFile(pdf_bytes),
        save=True
    )

    return True
