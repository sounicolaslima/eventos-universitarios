from django.contrib import admin
from .models import Categoria, Local, Evento, Ingresso, Compra

@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ('id', 'nome', 'descricao')
    list_display_links = ('id', 'nome')
    search_fields = ('nome', 'descricao')
    list_filter = ('nome',)
    list_per_page = 25

@admin.register(Local)
class LocalAdmin(admin.ModelAdmin):
    list_display = ('id', 'nome', 'endereco', 'capacidade')
    list_display_links = ('id', 'nome')
    search_fields = ('nome', 'endereco')
    list_filter = ('capacidade',)
    list_editable = ('capacidade',)
    list_per_page = 25

@admin.register(Evento)
class EventoAdmin(admin.ModelAdmin):
    list_display = ('id', 'titulo', 'data_evento', 'local', 'categoria', 'organizador', 'preco_base')
    list_display_links = ('id', 'titulo')
    search_fields = ('titulo', 'descricao', 'organizador__username')
    list_filter = ('categoria', 'local', 'data_evento', 'organizador')
    list_editable = ('preco_base',)
    list_per_page = 25
    date_hierarchy = 'data_evento'

@admin.register(Ingresso)
class IngressoAdmin(admin.ModelAdmin):
    list_display = ('id', 'evento', 'tipo', 'preco', 'quantidade_disponivel')
    list_display_links = ('id', 'evento')
    search_fields = ('evento__titulo', 'tipo')
    list_filter = ('tipo', 'evento__categoria')
    list_editable = ('preco', 'quantidade_disponivel')
    list_per_page = 25

@admin.register(Compra)
class CompraAdmin(admin.ModelAdmin):
    list_display = ('id', 'usuario', 'ingresso', 'quantidade', 'valor_total', 'status', 'data_compra')
    list_display_links = ('id', 'usuario')
    search_fields = ('usuario__username', 'usuario__email', 'ingresso__evento__titulo')
    list_filter = ('status', 'data_compra', 'ingresso__evento')
    list_editable = ('status',)
    list_per_page = 25
    date_hierarchy = 'data_compra'


# Customizando o header do Admin
admin.site.site_header = 'Eventos Universitários - Admin'
admin.site.site_title = 'Painel Administrativo'
admin.site.index_title = 'Bem-vindo ao Painel de Controle'