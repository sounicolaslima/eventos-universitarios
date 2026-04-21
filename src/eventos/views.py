from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.db.models import Q
from decimal import Decimal
from .models import Evento, Ingresso, Compra, Categoria, Local

def home(request):
    return render(request, 'eventos/home.html')

def lista_eventos(request):
    eventos = Evento.objects.all()
    categorias = Categoria.objects.all()
    
    q = request.GET.get('q')
    categoria_id = request.GET.get('categoria')
    data = request.GET.get('data')

    if q:
        eventos = eventos.filter(titulo__icontains=q)
    if categoria_id:
        eventos = eventos.filter(categoria_id=categoria_id)
    if data:
        eventos = eventos.filter(data_evento__date=data)
    
    return render(request, 'eventos/evento_list.html', {
        'eventos': eventos,
        'categorias': categorias
    })

def detalhe_evento(request, evento_id):
    evento = get_object_or_404(Evento, id=evento_id)
    ingressos = evento.ingresso_set.all()
    return render(request, 'eventos/evento_detail.html', {
        'evento': evento,
        'ingressos': ingressos
    })

@login_required
def comprar_ingresso(request, ingresso_id):
    ingresso = get_object_or_404(Ingresso, id=ingresso_id)

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

@login_required
def confirmar_compra(request, ingresso_id):
    if request.method != 'POST':
        return redirect('comprar_ingresso', ingresso_id=ingresso_id)

    try:
        quantidade = int(request.POST.get('quantidade', '1'))
    except (TypeError, ValueError):
        messages.error(request, 'Quantidade inválida para confirmar a compra.')
        return redirect('comprar_ingresso', ingresso_id=ingresso_id)

    if quantidade < 1:
        messages.error(request, 'A quantidade mínima para compra é 1 ingresso.')
        return redirect('comprar_ingresso', ingresso_id=ingresso_id)

    with transaction.atomic():
        ingresso = get_object_or_404(
            Ingresso.objects.select_for_update(),
            id=ingresso_id
        )

        if quantidade > ingresso.quantidade_disponivel:
            messages.error(request, 'Os ingressos ficaram indisponíveis antes da confirmação. Tente novamente.')
            return redirect('comprar_ingresso', ingresso_id=ingresso.id)

        valor_total = ingresso.preco * quantidade

        compra = Compra.objects.create(
            usuario=request.user,
            ingresso=ingresso,
            quantidade=quantidade,
            valor_total=valor_total,
            status='confirmada'
        )

        ingresso.quantidade_disponivel -= quantidade
        ingresso.save(update_fields=['quantidade_disponivel'])

    messages.success(request, 'Compra simulada confirmada com sucesso!')
    return render(request, 'eventos/compra_sucesso.html', {
        'compra': compra,
    })

@login_required
def meu_historico(request):
    compras = Compra.objects.filter(usuario=request.user).order_by('-data_compra')
    return render(request, 'eventos/meu_historico.html', {'compras': compras})

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
def editar_evento(request, evento_id):
    """Edita um evento existente"""
    evento = get_object_or_404(Evento, id=evento_id, organizador=request.user)
    ingressos = evento.ingresso_set.all()
    
    if request.method == 'POST':
        evento.titulo = request.POST.get('titulo')
        evento.descricao = request.POST.get('descricao')
        evento.data_evento = request.POST.get('data_evento')
        evento.local_id = request.POST.get('local')
        evento.categoria_id = request.POST.get('categoria')
        evento.preco_base = request.POST.get('preco_base') or 0
        
        if request.FILES.get('imagem'):
            evento.imagem = request.FILES.get('imagem')
        
        evento.save()
        messages.success(request, 'Evento atualizado com sucesso!')
        return redirect('meus_eventos')
    
    locais = Local.objects.all()
    categorias = Categoria.objects.all()
    return render(request, 'eventos/editar_evento.html', {
        'evento': evento,
        'locais': locais,
        'categorias': categorias,
        'ingressos': ingressos
    })

@login_required
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
            
        except Exception as e:
            messages.error(request, f'Erro ao atualizar evento: {str(e)}')
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
        except Exception as e:
            messages.error(request, f'Erro ao criar ingresso: {str(e)}')
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