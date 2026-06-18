from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.utils import timezone
from django.utils.dateparse import parse_date
from django.http import FileResponse, Http404, HttpResponseForbidden
from django.views.decorators.http import require_http_methods

from decimal import Decimal, InvalidOperation

from .models import Evento, Ingresso, Compra, Categoria, Local
from .tasks import schedule_event_reminder, generate_certificate


# ==========================
# HOME
# ==========================

def home(request):
    return render(request, 'eventos/home.html')


# ==========================
# FILTROS AUXILIARES
# ==========================

def filtrar_por_data(queryset, campo, valor):
    data = parse_date(valor) if valor else None
    if not data:
        return queryset
    return queryset.filter(**{campo: data})


def filtrar_por_preco(queryset, campo, valor):
    if not valor:
        return queryset
    try:
        preco = Decimal(valor)
    except (InvalidOperation, ValueError):
        return queryset
    return queryset.filter(**{campo: preco})


# ==========================
# LISTA EVENTOS
# ==========================

def lista_eventos(request):
    eventos = Evento.objects.all()
    categorias = Categoria.objects.all()

    q = request.GET.get('q')
    categoria_id = request.GET.get('categoria')
    data = request.GET.get('data')
    data_inicio = request.GET.get('data_inicio') or data
    data_fim = request.GET.get('data_fim') or data
    preco_min = request.GET.get('preco_min')
    preco_max = request.GET.get('preco_max')

    if q:
        eventos = eventos.filter(titulo__icontains=q)

    if categoria_id:
        eventos = eventos.filter(categoria_id=categoria_id)

    eventos = filtrar_por_data(eventos, 'data_evento__date__gte', data_inicio)
    eventos = filtrar_por_data(eventos, 'data_evento__date__lte', data_fim)
    eventos = filtrar_por_preco(eventos, 'preco_base__gte', preco_min)
    eventos = filtrar_por_preco(eventos, 'preco_base__lte', preco_max)

    return render(request, 'eventos/evento_list.html', {
        'eventos': eventos,
        'categorias': categorias
    })


# ==========================
# DETALHE EVENTO
# ==========================

def detalhe_evento(request, evento_id):
    evento = get_object_or_404(Evento, id=evento_id)
    ingressos = evento.ingresso_set.all()

    return render(request, 'eventos/evento_detail.html', {
        'evento': evento,
        'ingressos': ingressos,
        'now': timezone.now()
    })


# ==========================
# COMPRA DE INGRESSO
# ==========================

@login_required
def comprar_ingresso(request, ingresso_id):
    ingresso = get_object_or_404(Ingresso, id=ingresso_id)

    if ingresso.evento.data_evento <= timezone.now():
        messages.error(request, 'Não é possível comprar ingressos para eventos já encerrados.')
        return redirect('detalhe_evento', evento_id=ingresso.evento.id)

    if request.method == 'POST':
        quantidade_raw = request.POST.get('quantidade', '1')

        try:
            quantidade = int(quantidade_raw)
        except (TypeError, ValueError):
            messages.error(request, 'Informe uma quantidade válida.')
            return render(request, 'eventos/comprar_ingresso.html', {
                'ingresso': ingresso,
                'quantidade': quantidade_raw
            })

        if quantidade < 1:
            messages.error(request, 'A quantidade mínima para compra é 1 ingresso.')
            return render(request, 'eventos/comprar_ingresso.html', {
                'ingresso': ingresso,
                'quantidade': quantidade
            })

        if quantidade > ingresso.quantidade_disponivel:
            messages.error(request, 'Quantidade indisponível para este ingresso.')
            return render(request, 'eventos/comprar_ingresso.html', {
                'ingresso': ingresso,
                'quantidade': quantidade
            })

        valor_total = ingresso.preco * quantidade

        return render(request, 'eventos/revisar_compra.html', {
            'ingresso': ingresso,
            'quantidade': quantidade,
            'valor_total': valor_total,
        })

    return render(request, 'eventos/comprar_ingresso.html', {
        'ingresso': ingresso,
        'quantidade': 1
    })


# ==========================
# CONFIRMAR COMPRA
# ==========================

@login_required
def confirmar_compra(request, ingresso_id):

    if request.method != 'POST':
        return redirect(
            'comprar_ingresso',
            ingresso_id=ingresso_id
        )

    try:
        quantidade = int(
            request.POST.get('quantidade', '1')
        )
    except (TypeError, ValueError):

        messages.error(
            request,
            'Quantidade inválida.'
        )

        return redirect(
            'comprar_ingresso',
            ingresso_id=ingresso_id
        )

    with transaction.atomic():

        ingresso = get_object_or_404(
            Ingresso.objects.select_for_update(),
            id=ingresso_id
        )

        if ingresso.evento.data_evento <= timezone.now():

            messages.error(
                request,
                'Não é possível comprar ingressos para eventos já encerrados.'
            )

            return redirect(
                'detalhe_evento',
                evento_id=ingresso.evento.id
            )

        if quantidade < 1:

            messages.error(
                request,
                'Quantidade inválida.'
            )

            return redirect(
                'comprar_ingresso',
                ingresso_id=ingresso_id
            )

        if quantidade > ingresso.quantidade_disponivel:

            messages.error(
                request,
                'Ingressos indisponíveis.'
            )

            return redirect(
                'comprar_ingresso',
                ingresso_id=ingresso_id
            )

        compra = Compra.objects.create(
            usuario=request.user,
            ingresso=ingresso,
            quantidade=quantidade,
            valor_total=ingresso.preco * quantidade,
            status='confirmada'
        )

        ingresso.quantidade_disponivel -= quantidade
        ingresso.save(
            update_fields=[
                'quantidade_disponivel'
            ]
        )

    schedule_event_reminder(compra)

    return redirect(
        'confirmacao_compra',
        codigo_uuid=compra.codigo_uuid
    )


# ==========================
# CONFIRMAÇÃO
# ==========================

@login_required
@require_http_methods(["GET"])
def confirmacao_compra(request, codigo_uuid):
    compra = get_object_or_404(
        Compra,
        codigo_uuid=codigo_uuid,
        usuario=request.user
    )

    return render(request, 'eventos/compra_sucesso.html', {
        'compra': compra
    })


# ==========================
# HISTÓRICO
# ==========================

@login_required
def meu_historico(request):
    compras = Compra.objects.filter(
        usuario=request.user
    ).order_by('-data_compra')

    return render(request, 'eventos/meu_historico.html', {
        'compras': compras
    })


# ==========================
# DOWNLOAD CERTIFICADO
# ==========================

@login_required
def download_certificado(request, compra_id):
    compra = get_object_or_404(
        Compra,
        id=compra_id,
        usuario=request.user,
        status='presente'
    )

    if not compra.certificado:
        raise Http404("Certificado não encontrado.")

    return FileResponse(
        compra.certificado.open('rb'),
        as_attachment=True,
        filename=f'certificado-{compra.codigo_uuid}.pdf',
        content_type='application/pdf'
    )


# ==========================
# ORG: CRIAR EVENTO
# ==========================

@login_required
def criar_evento(request):
    if request.method == 'POST':
        titulo = request.POST.get('titulo')
        descricao = request.POST.get('descricao')
        data_evento = request.POST.get('data_evento')
        categoria_id = request.POST.get('categoria')

        if not all([titulo, descricao, data_evento, categoria_id]):
            messages.error(request, 'Preencha todos os campos obrigatórios.')
            return redirect('criar_evento')

        categoria = get_object_or_404(Categoria, id=categoria_id)

        Evento.objects.create(
            titulo=titulo,
            descricao=descricao,
            data_evento=data_evento,
            categoria=categoria,
            organizador=request.user
        )

        messages.success(request, 'Evento criado com sucesso!')
        return redirect('meus_eventos')

    return render(request, 'eventos/criar_evento.html')


# ==========================
# ORG: MEUS EVENTOS
# ==========================

@login_required
def meus_eventos(request):
    eventos = Evento.objects.filter(organizador=request.user)
    return render(request, 'eventos/meus_eventos.html', {
        'eventos': eventos
    })


# ==========================
# QR CODE
# ==========================

@login_required
def validar_qr(request, uuid):

    if not request.user.is_staff:
        return HttpResponseForbidden("Apenas organizadores.")

    try:
        compra = Compra.objects.get(codigo_uuid=uuid)
    except Compra.DoesNotExist:
        messages.error(request, 'QR Code inválido.')
        return redirect('home')

    if compra.status == 'presente':
        messages.warning(request, 'QR já utilizado.')
        return redirect('home')

    compra.status = 'presente'
    compra.save(update_fields=['status'])

    generate_certificate.delay(compra.id)

    messages.success(request, 'Presença confirmada!')
    return redirect('home')

@login_required
def editar_evento(request, evento_id):

    evento = get_object_or_404(
        Evento,
        id=evento_id,
        organizador=request.user
    )

    if request.method == 'POST':

        try:

            titulo = request.POST.get('titulo')
            descricao = request.POST.get('descricao')
            data_evento = request.POST.get('data_evento')
            categoria_id = request.POST.get('categoria')
            preco_base = request.POST.get('preco_base')

            local_nome = request.POST.get('local_nome')
            local_endereco = request.POST.get(
                'local_endereco',
                ''
            )

            if not all([
                titulo,
                descricao,
                data_evento,
                categoria_id,
                preco_base,
                local_nome
            ]):
                return redirect(
                    'editar_evento',
                    evento_id=evento.id
                )

            categoria = get_object_or_404(
                Categoria,
                id=categoria_id
            )

            local, _ = Local.objects.get_or_create(
                nome=local_nome,
                defaults={
                    'capacidade': 100,
                    'endereco': local_endereco
                }
            )

            evento.titulo = titulo
            evento.descricao = descricao
            evento.data_evento = data_evento
            evento.categoria = categoria
            evento.preco_base = preco_base
            evento.local = local

            if request.FILES.get('imagem'):
                evento.imagem = request.FILES['imagem']

            evento.save()

            messages.success(
                request,
                'Evento atualizado.'
            )

            return redirect(
                'meus_eventos'
            )

        except Exception:

            messages.error(
                request,
                'Erro ao atualizar evento.'
            )

            return redirect(
                'editar_evento',
                evento_id=evento.id
            )

    return render(
        request,
        'eventos/editar_evento.html',
        {
            'evento': evento
        }
    )


@login_required
def excluir_evento(request, evento_id):
    evento = get_object_or_404(
        Evento,
        id=evento_id,
        organizador=request.user
    )

    if request.method == 'POST':
        evento.delete()
        messages.success(request, 'Evento excluído com sucesso.')
        return redirect('meus_eventos')

    return render(
        request,
        'eventos/excluir_evento.html',
        {'evento': evento}
    )


@login_required
def adicionar_ingresso(request, evento_id):

    evento = get_object_or_404(
        Evento,
        id=evento_id,
        organizador=request.user
    )

    if request.method == 'POST':

        tipo = request.POST.get('tipo')
        preco = request.POST.get('preco')
        quantidade = request.POST.get('quantidade')

        if not all([
            tipo,
            preco,
            quantidade
        ]):
            return redirect(
                'adicionar_ingresso',
                evento_id=evento.id
            )

        try:

            Ingresso.objects.create(
                evento=evento,
                tipo=tipo,
                preco=Decimal(preco),
                quantidade_disponivel=int(
                    quantidade
                )
            )

            messages.success(
                request,
                'Ingresso criado com sucesso.'
            )

            return redirect(
                'editar_evento',
                evento_id=evento.id
            )

        except (
            ValueError,
            InvalidOperation,
            TypeError
        ):

            messages.error(
                request,
                'Dados inválidos.'
            )

            return redirect(
                'adicionar_ingresso',
                evento_id=evento.id
            )

    return render(
        request,
        'eventos/adicionar_ingresso.html',
        {
            'evento': evento
        }
    )


@login_required
def editar_ingresso(request, ingresso_id):

    ingresso = get_object_or_404(
        Ingresso,
        id=ingresso_id,
        evento__organizador=request.user
    )

    if request.method == 'POST':

        try:

            ingresso.tipo = request.POST.get(
                'tipo',
                ingresso.tipo
            )

            ingresso.preco = Decimal(
                request.POST.get(
                    'preco',
                    ingresso.preco
                )
            )

            ingresso.quantidade_disponivel = int(
                request.POST.get(
                    'quantidade',
                    ingresso.quantidade_disponivel
                )
            )

            ingresso.save()

            messages.success(
                request,
                'Ingresso atualizado.'
            )

            return redirect(
                'editar_evento',
                evento_id=ingresso.evento.id
            )

        except (
            ValueError,
            InvalidOperation,
            TypeError
        ):

            messages.error(
                request,
                'Dados inválidos.'
            )

            return redirect(
                'editar_ingresso',
                ingresso_id=ingresso.id
            )

    return render(
        request,
        'eventos/editar_ingresso.html',
        {
            'ingresso': ingresso
        }
    )

@login_required
def excluir_ingresso(request, ingresso_id):
    ingresso = get_object_or_404(
        Ingresso,
        id=ingresso_id,
        evento__organizador=request.user
    )

    if request.method == 'POST':
        evento_id = ingresso.evento.id
        ingresso.delete()

        messages.success(
            request,
            'Ingresso excluído com sucesso.'
        )

        return redirect(
            'editar_evento',
            evento_id=evento_id
        )

    return render(
        request,
        'eventos/excluir_ingresso.html',
        {'ingresso': ingresso}
    )