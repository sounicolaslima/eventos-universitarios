import os
import django
from datetime import datetime, timedelta

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'eventos_universitarios.settings')
django.setup()

from eventos.models import Categoria, Local, Evento, Ingresso
from django.contrib.auth.models import User

def criar_dados():
    print("=" * 50)
    print("Criando dados de teste...")
    print("=" * 50)
    
    # Criar usuário organizador
    organizador, created = User.objects.get_or_create(
        username='organizador',
        defaults={
            'email': 'organizador@eventos.com',
            'password': '123456'
        }
    )
    if created:
        organizador.set_password('123456')
        organizador.save()
        print("✓ Usuário organizador criado (login: organizador / senha: 123456)")
    else:
        print("! Usuário organizador já existe")
    
    # Criar categorias
    categorias_lista = [
        'Palestra', 'Workshop', 'Congresso', 'Seminário', 'Simpósio'
    ]
    
    for nome in categorias_lista:
        cat, created = Categoria.objects.get_or_create(
            nome=nome,
            defaults={'descricao': f'{nome}s acadêmicos e profissionais'}
        )
        print(f"✓ Categoria: {cat.nome}")
    
    # Criar locais
    locais_data = [
        {'nome': 'Auditório Principal', 'endereco': 'Campus Central - Bloco A', 'capacidade': 200},
        {'nome': 'Laboratório 101', 'endereco': 'Campus Sul - Bloco C', 'capacidade': 30},
        {'nome': 'Centro de Convenções', 'endereco': 'Centro da Cidade', 'capacidade': 1000},
        {'nome': 'Teatro Universitário', 'endereco': 'Campus Norte', 'capacidade': 500},
    ]
    
    for local_data in locais_data:
        local, created = Local.objects.get_or_create(
            nome=local_data['nome'],
            defaults=local_data
        )
        print(f"✓ Local: {local.nome}")
    
    # Criar eventos
    eventos_data = [
        {
            'titulo': 'Palestra: Inteligência Artificial na Educação',
            'descricao': 'Uma palestra sobre as aplicações de IA no ensino superior.',
            'dias': 7,
            'local': 'Auditório Principal',
            'categoria': 'Palestra',
            'preco_base': 25.00,
            'ingressos': [
                ('inteira', 25.00, 100),
                ('meia', 12.50, 50),
            ]
        },
        {
            'titulo': 'Workshop: Desenvolvimento Web com Django',
            'descricao': 'Workshop prático de 2 dias sobre Django e Bootstrap.',
            'dias': 14,
            'local': 'Laboratório 101',
            'categoria': 'Workshop',
            'preco_base': 50.00,
            'ingressos': [
                ('inteira', 50.00, 30),
                ('meia', 25.00, 15),
            ]
        },
        {
            'titulo': 'Congresso de Tecnologia 2025',
            'descricao': 'Maior congresso de tecnologia com palestrantes nacionais.',
            'dias': 30,
            'local': 'Centro de Convenções',
            'categoria': 'Congresso',
            'preco_base': 150.00,
            'ingressos': [
                ('inteira', 150.00, 500),
                ('meia', 75.00, 200),
                ('vip', 300.00, 50),
            ]
        },
        {
            'titulo': 'Seminário de Empreendedorismo',
            'descricao': 'Aprenda com empreendedores de sucesso.',
            'dias': 21,
            'local': 'Teatro Universitário',
            'categoria': 'Seminário',
            'preco_base': 30.00,
            'ingressos': [
                ('inteira', 30.00, 60),
                ('meia', 15.00, 40),
            ]
        },
    ]
    
    for ev_data in eventos_data:
        local = Local.objects.get(nome=ev_data['local'])
        categoria = Categoria.objects.get(nome=ev_data['categoria'])
        
        evento, created = Evento.objects.get_or_create(
            titulo=ev_data['titulo'],
            defaults={
                'descricao': ev_data['descricao'],
                'data_evento': datetime.now() + timedelta(days=ev_data['dias']),
                'local': local,
                'categoria': categoria,
                'preco_base': ev_data['preco_base'],
                'organizador': organizador,
            }
        )
        
        if created:
            print(f"\n✓ Evento criado: {evento.titulo}")
            for tipo, preco, qtd in ev_data['ingressos']:
                ingresso = Ingresso.objects.create(
                    evento=evento,
                    tipo=tipo,
                    preco=preco,
                    quantidade_disponivel=qtd
                )
                print(f"  ✓ Ingresso {tipo}: R$ {preco} ({qtd} disponíveis)")
        else:
            print(f"\n! Evento já existe: {evento.titulo}")
    
    print("\n" + "=" * 50)
    print("✅ DADOS CRIADOS COM SUCESSO!")
    print("=" * 50)
    print("\n📋 ACESSOS:")
    print("   Site: http://127.0.0.1:8000")
    print("   Admin: http://127.0.0.1:8000/admin")
    print("   Login admin: organizador / 123456")
    print("\n🎫 Agora você pode:")
    print("   1. Criar um usuário comum (Cadastrar)")
    print("   2. Fazer login")
    print("   3. Comprar ingressos para os eventos")
    print("   4. Ver seu histórico de compras")

if __name__ == "__main__":
    criar_dados()