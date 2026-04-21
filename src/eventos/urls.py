from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('eventos/', views.lista_eventos, name='lista_eventos'),
    path('evento/<int:evento_id>/', views.detalhe_evento, name='detalhe_evento'),
    path('comprar/<int:ingresso_id>/', views.comprar_ingresso, name='comprar_ingresso'),
    path('meu-historico/', views.meu_historico, name='meu_historico'),
    
    # URLs do Organizador
    path('organizador/eventos/', views.meus_eventos, name='meus_eventos'),
    path('organizador/evento/criar/', views.criar_evento, name='criar_evento'),
    path('organizador/evento/editar/<int:evento_id>/', views.editar_evento, name='editar_evento'),
    path('organizador/evento/excluir/<int:evento_id>/', views.excluir_evento, name='excluir_evento'),
    path('organizador/ingresso/adicionar/<int:evento_id>/', views.adicionar_ingresso, name='adicionar_ingresso'),
    path('organizador/ingresso/editar/<int:ingresso_id>/', views.editar_ingresso, name='editar_ingresso'),
    path('organizador/ingresso/excluir/<int:ingresso_id>/', views.excluir_ingresso, name='excluir_ingresso'),
]