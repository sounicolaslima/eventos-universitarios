from django import template
from django.contrib.auth.models import User

register = template.Library()

@register.filter
def is_admin(user):
    """Verifica se o usuário é administrador (staff ou superuser)"""
    if user.is_authenticated:
        return user.is_staff or user.is_superuser
    return False

@register.filter
def is_superuser(user):
    """Verifica se o usuário é superusuário"""
    if user.is_authenticated:
        return user.is_superuser
    return False

@register.filter
def is_staff(user):
    """Verifica se o usuário é staff"""
    if user.is_authenticated:
        return user.is_staff
    return False

@register.simple_tag
def get_user_badge(user):
    """Retorna o badge HTML apropriado para o usuário"""
    if not user.is_authenticated:
        return ''
    
    if user.is_superuser:
        return '<span class="badge bg-gradient-gold ms-2" style="background: linear-gradient(135deg, #f59e0b, #d97706);"><i class="fas fa-crown me-1"></i>Super Admin</span>'
    elif user.is_staff:
        return '<span class="badge bg-gradient-primary ms-2"><i class="fas fa-shield-alt me-1"></i>Admin</span>'
    return ''

@register.filter
def user_role_badge(user):
    """Retorna o badge de papel do usuário"""
    if not user.is_authenticated:
        return '<span class="badge bg-secondary">Visitante</span>'
    
    if user.is_superuser:
        return '<span class="badge bg-danger"><i class="fas fa-crown me-1"></i>Super Admin</span>'
    elif user.is_staff:
        return '<span class="badge bg-warning text-dark"><i class="fas fa-shield-alt me-1"></i>Admin</span>'
    else:
        return '<span class="badge bg-secondary"><i class="fas fa-user me-1"></i>Usuário</span>'