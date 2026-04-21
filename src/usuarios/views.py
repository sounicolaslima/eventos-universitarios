from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from django.contrib.auth.forms import UserCreationForm
from django import forms
from django.contrib.auth.models import User
from eventos.models import Compra

class RegistroForm(UserCreationForm):
    email = forms.EmailField(required=True)
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

def registro(request):
    if request.method == 'POST':
        form = RegistroForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, 'Cadastro realizado com sucesso! Faça login.')
            return redirect('login')
    else:
        form = RegistroForm()
    return render(request, 'usuarios/registro.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            messages.success(request, f'Bem-vindo, {username}!')
            return redirect('dashboard')
        messages.error(request, 'Usuário ou senha inválidos')
    return render(request, 'usuarios/login.html')

def logout_view(request):
    logout(request)
    messages.info(request, 'Você saiu do sistema.')
    return redirect('home')

def dashboard(request):
    if not request.user.is_authenticated:
        return redirect('login')
    
    from eventos.models import Compra
    
    compras = Compra.objects.filter(usuario=request.user)
    
    # Calcular estatísticas
    eventos_presentes = compras.filter(status='presente').count()
    certificados_count = compras.exclude(certificado='').filter(status='presente').count()
    
    context = {
        'total_compras': compras.count(),
        'eventos_presentes': eventos_presentes,
        'certificados_count': certificados_count,
        'compras_recentes': compras.order_by('-data_compra')[:5],
    }
    return render(request, 'usuarios/dashboard.html', context)