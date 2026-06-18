from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from decimal import Decimal, InvalidOperation
from django.utils import timezone
from django.utils.dateparse import parse_date
from .models import Evento, Ingresso, Compra, Categoria, Local
from django.http import HttpResponseForbidden
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required

# Template constants
TEMPLATE_COMPRAR_INGRESSO = 'eventos/comprar_ingresso.html'

def home(request):
    return render(request, 'eventos/home.html')


def filtrar_por_data(eventos, campo, valor):
    data = parse_date(valor) if valor else None
    if not data:
        return eventos
    return eventos.filter(**{campo: data})


def filtrar_por_preco(eventos, campo, valor):
    if not valor:
        return eventos
    try:
        preco = Decimal(valor)
    except (InvalidOperation, ValueError):
        return eventos
    return eventos.filter(**{campo: preco})


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

def detalhe_evento(request, evento_id):
    evento = get_object_or_404(Evento, id=evento_id)
    ingressos = evento.ingresso_set.all()
    return render(request, 'eventos/evento_detail.html', {
        'evento': evento,
        'ingressos': ingressos,
        'now': timezone.now()
    })

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
            return render(request, TEMPLATE_COMPRAR_INGRESSO, {
                'ingresso': ingresso,
                'quantidade': quantidade_raw
            })

        if quantidade < 1:
            messages.error(request, 'A quantidade mínima para compra é 1 ingresso.')
            return render(request, TEMPLATE_COMPRAR_INGRESSO, {
                'ingresso': ingresso,
                'quantidade': quantidade
            })

        if quantidade > ingresso.quantidade_disponivel:
            messages.error(request, 'Quantidade indisponível para este ingresso.')
            return render(request, TEMPLATE_COMPRAR_INGRESSO, {
                'ingresso': ingresso,
                'quantidade': quantidade
            })

        valor_total = ingresso.preco * quantidade

        return render(request, 'eventos/revisar_compra.html', {
            'ingresso': ingresso,
            'quantidade': quantidade,
            'valor_total': valor_total,
        })

    return render(request, TEMPLATE_COMPRAR_INGRESSO, {
        'ingresso': ingresso,
        'quantidade': 1
    })

@login_required
def confirmar_compra(request, ingresso_id):
    if request.method != 'POST':
        return redirect('comprar_ingresso', ingresso_id=ingresso_id)

    # Validação da quantidade
    try:
        quantidade = int(request.POST.get('quantidade', '1'))
    except (TypeError, ValueError):
        messages.error(request, 'Quantidade inválida para confirmar a compra.')
        return redirect('comprar_ingresso', ingresso_id=ingresso_id)

    if quantidade < 1:
        messages.error(request, 'A quantidade mínima para compra é 1 ingresso.')
        return redirect('comprar_ingresso', ingresso_id=ingresso_id)

    with transaction.atomic():
        # 🔒 trava o registro no banco (evita duas pessoas comprarem ao mesmo tempo)
        ingresso = get_object_or_404(
            Ingresso.objects.select_for_update(),
            id=ingresso_id
        )

        # 🚫 evento já aconteceu
        if ingresso.evento.data_evento <= timezone.now():
            messages.error(request, 'A compra não pode ser concluída porque o evento já foi encerrado.')
            return redirect('detalhe_evento', evento_id=ingresso.evento.id)

        # 🚫 sem estoque
        if quantidade > ingresso.quantidade_disponivel:
            messages.error(request, 'Os ingressos ficaram indisponíveis antes da confirmação. Tente novamente.')
            return redirect('comprar_ingresso', ingresso_id=ingresso.id)

        # ✅ cria a compra
        valor_total = ingresso.preco * quantidade

        compra = Compra.objects.create(
            usuario=request.user,
            ingresso=ingresso,
            quantidade=quantidade,
            valor_total=valor_total,
            status='confirmada'
        )

        # ✅ atualiza estoque
        ingresso.quantidade_disponivel -= quantidade
        ingresso.save(update_fields=['quantidade_disponivel'])

    # fora da transação
    messages.success(request, 'Compra simulada confirmada com sucesso!')

    return render(request, 'eventos/compra_sucesso.html', {
        'compra': compra,
    })

@login_required
def meu_historico(request):
    compras = Compra.objects.filter(usuario=request.user).select_related(
        'ingresso',
        'ingresso__evento'
    ).order_by('-data_compra')

    return render(request, 'eventos/meu_historico.html', {
        'compras': compras
    })

# ==================== VIEWS DO ORGANIZADOR ====================

@login_required
def meus_eventos(request):
    """Lista eventos do organizador logado"""
    eventos = Evento.objects.filter(organizador=request.user).order_by('-data_evento')
    return render(request, 'eventos/meus_eventos.html', {'eventos': eventos})

@login_required
def criar_evento(request):
    """Cria um novo evento"""
    if request.method == 'POST':
        titulo = request.POST.get('titulo')
        descricao = request.POST.get('descricao')
        data_evento = request.POST.get('data_evento')
        local_nome = request.POST.get('local_nome')
        local_endereco = request.POST.get('local_endereco', '')
        categoria_id = request.POST.get('categoria')
        preco_base = request.POST.get('preco_base')
        imagem = request.FILES.get('imagem')
        
        # Validações
        if not titulo or not descricao or not data_evento or not local_nome or not categoria_id:
            messages.error(request, 'Preencha todos os campos obrigatórios')
            return redirect('criar_evento')
        
        # Criar ou obter local
        local, created = Local.objects.get_or_create(
            nome=local_nome,
            defaults={'endereco': local_endereco, 'capacidade': 100}
        )
        
        if created:
            messages.info(request, f'Local "{local_nome}" foi cadastrado automaticamente.')
        
        categoria = get_object_or_404(Categoria, id=categoria_id)
        
        evento = Evento.objects.create(
            titulo=titulo,
            descricao=descricao,
            data_evento=data_evento,
            local=local,
            categoria=categoria,
            preco_base=preco_base or 0,
            imagem=imagem,
            organizador=request.user
        )
        
        messages.success(request, f'Evento "{evento.titulo}" criado com sucesso!')
        return redirect('editar_evento', evento_id=evento.id)
    
    locais = Local.objects.all()
    categorias = Categoria.objects.all()
    return render(request, 'eventos/criar_evento.html', {
        'locais': locais,
        'categorias': categorias
    })

@login_required
@require_http_methods(["GET", "POST"])
def editar_evento(request, evento_id):
    """Edita um evento existente"""
    evento = get_object_or_404(Evento, id=evento_id, organizador=request.user)
    ingressos = evento.ingresso_set.all()
    
    if request.method == 'POST':
        try:
            # Pegar dados do formulário
            titulo = request.POST.get('titulo')
            descricao = request.POST.get('descricao')
            data_evento = request.POST.get('data_evento')
            categoria_id = request.POST.get('categoria')
            preco_base = request.POST.get('preco_base')
            
            # Dados do local
            local_nome = request.POST.get('local_nome')
            local_endereco = request.POST.get('local_endereco', '')
            
            # Validações
            if not titulo or not descricao or not data_evento or not local_nome or not categoria_id:
                messages.error(request, 'Preencha todos os campos obrigatórios')
                return redirect('editar_evento', evento_id=evento.id)
            
            # Criar ou obter local
            local, created = Local.objects.get_or_create(
                nome=local_nome.strip(),
                defaults={'endereco': local_endereco, 'capacidade': 100}
            )
            
            # Atualizar evento
            evento.titulo = titulo
            evento.descricao = descricao
            evento.data_evento = data_evento
            evento.categoria_id = categoria_id
            evento.preco_base = preco_base or 0
            evento.local = local  # IMPORTANTE: atribuir o local ao evento
            
            # Atualizar imagem se enviada
            if request.FILES.get('imagem'):
                evento.imagem = request.FILES.get('imagem')
            
            evento.save()
            
            if created:
                messages.success(request, f'Evento atualizado e local "{local_nome}" foi criado automaticamente!')
            else:
                messages.success(request, 'Evento atualizado com sucesso!')
                
            return redirect('meus_eventos')
            
        except Exception:
            messages.error(request, 'Erro ao atualizar evento. Tente novamente.')
            return redirect('editar_evento', evento_id=evento.id)
    
    locais = Local.objects.all()
    categorias = Categoria.objects.all()
    return render(request, 'eventos/editar_evento.html', {
        'evento': evento,
        'locais': locais,
        'categorias': categorias,
        'ingressos': ingressos
    })

@login_required
def excluir_evento(request, evento_id):
    """Exclui um evento"""
    evento = get_object_or_404(Evento, id=evento_id, organizador=request.user)
    
    if request.method == 'POST':
        titulo = evento.titulo
        evento.delete()
        messages.success(request, f'Evento "{titulo}" excluído com sucesso!')
        return redirect('meus_eventos')
    
    return render(request, 'eventos/excluir_evento.html', {'evento': evento})

@login_required
def adicionar_ingresso(request, evento_id):
    """Adiciona um ingresso a um evento"""
    evento = get_object_or_404(Evento, id=evento_id, organizador=request.user)
    
    if request.method == 'POST':
        tipo = request.POST.get('tipo')
        preco = request.POST.get('preco')
        quantidade = request.POST.get('quantidade')
        
        # Validações
        if not tipo or not preco or not quantidade:
            messages.error(request, 'Preencha todos os campos do ingresso')
            return redirect('adicionar_ingresso', evento_id=evento.id)
        
        try:
            preco = float(preco)
            quantidade = int(quantidade)
            
            ingresso = Ingresso.objects.create(
                evento=evento,
                tipo=tipo,
                preco=preco,
                quantidade_disponivel=quantidade
            )
            messages.success(request, f'Ingresso {ingresso.get_tipo_display()} adicionado com sucesso!')
            return redirect('editar_evento', evento_id=evento.id)
        except Exception:
            messages.error(request, 'Erro ao criar ingresso. Tente novamente.')
            return redirect('adicionar_ingresso', evento_id=evento.id)
    
    return render(request, 'eventos/adicionar_ingresso.html', {'evento': evento})

@login_required
def editar_ingresso(request, ingresso_id):
    """Edita um ingresso"""
    ingresso = get_object_or_404(Ingresso, id=ingresso_id, evento__organizador=request.user)
    
    if request.method == 'POST':
        ingresso.tipo = request.POST.get('tipo')
        ingresso.preco = request.POST.get('preco')
        ingresso.quantidade_disponivel = request.POST.get('quantidade')
        ingresso.save()
        messages.success(request, 'Ingresso atualizado com sucesso!')
        return redirect('editar_evento', evento_id=ingresso.evento.id)
    
    return render(request, 'eventos/editar_ingresso.html', {'ingresso': ingresso})

@login_required
def excluir_ingresso(request, ingresso_id):
    """Exclui um ingresso"""
    ingresso = get_object_or_404(Ingresso, id=ingresso_id, evento__organizador=request.user)
    evento_id = ingresso.evento.id
    
    if request.method == 'POST':
        ingresso.delete()
        messages.success(request, 'Ingresso excluído com sucesso!')
        return redirect('editar_evento', evento_id=evento_id)
    
    return render(request, 'eventos/excluir_ingresso.html', {'ingresso': ingresso})

@login_required
def validar_qr(request, uuid):

    # Apenas organizador pode validar
    if not request.user.is_staff:
        return HttpResponseForbidden(
            'Apenas organizadores podem validar presença.'
        )

    try:
        compra = Compra.objects.get(codigo_uuid=uuid)

    except Compra.DoesNotExist:
        messages.error(request, 'QR Code inválido.')
        return redirect('home')

    # Impede reutilização
    if compra.status == 'presente':
        messages.warning(
            request,
            'Este QR Code já foi utilizado.'
        )

        return redirect('home')

    # Marca presença
    compra.status = 'presente'
    compra.save()

    messages.success(
        request,
        f'Presença confirmada para {compra.usuario.username}!'
    )

    return redirect('home')
