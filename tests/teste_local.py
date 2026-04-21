from django.test import TestCase

from eventos.models import Local


class LocalModelTest(TestCase):
    def test_criacao_local_valido_salva_campos_corretamente(self):
        local = Local.objects.create(
            nome='Auditório Central',
            endereco='Av. Universitária, 1000',
            capacidade=250
        )

        self.assertIsNotNone(local.id)
        self.assertEqual(local.nome, 'Auditório Central')
        self.assertEqual(local.endereco, 'Av. Universitária, 1000')
        self.assertEqual(local.capacidade, 250)

    def test_local_str_retorna_nome(self):
        local = Local.objects.create(nome='Sala 101')

        self.assertEqual(str(local), 'Sala 101')

    def test_local_capacidade_padrao_e_100(self):
        local = Local.objects.create(nome='Sala Verde')

        self.assertEqual(local.capacidade, 100)

    def test_local_endereco_opcional(self):
        local = Local.objects.create(nome='Auditório B', capacidade=80)

        self.assertIsNone(local.endereco)

    def test_get_or_create_local_cria_novo_quando_nao_existe(self):
        local, created = Local.get_or_create_local(
            nome='Quadra Poliesportiva',
            endereco='Bloco C',
            capacidade=500
        )

        self.assertTrue(created)
        self.assertEqual(local.nome, 'Quadra Poliesportiva')
        self.assertEqual(local.endereco, 'Bloco C')
        self.assertEqual(local.capacidade, 500)

    def test_get_or_create_local_retorna_existente_sem_duplicar(self):
        Local.objects.create(nome='Biblioteca', capacidade=150)

        local, created = Local.get_or_create_local(nome='Biblioteca')

        self.assertFalse(created)
        self.assertEqual(local.capacidade, 150)
        self.assertEqual(Local.objects.filter(nome='Biblioteca').count(), 1)

    def test_local_meta_ordering_por_nome(self):
        Local.objects.create(nome='Sala Z')
        Local.objects.create(nome='Sala A')
        Local.objects.create(nome='Sala M')

        nomes = list(Local.objects.values_list('nome', flat=True))
        self.assertEqual(nomes, ['Sala A', 'Sala M', 'Sala Z'])
