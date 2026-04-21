from django.test import TestCase

from eventos.models import Categoria


class CategoriaModelTest(TestCase):
    def test_criacao_categoria_valida_salva_campos_corretamente(self):
        categoria = Categoria.objects.create(
            nome='Workshop',
            descricao='Eventos práticos e mão na massa'
        )

        self.assertIsNotNone(categoria.id)
        self.assertEqual(categoria.nome, 'Workshop')
        self.assertEqual(categoria.descricao, 'Eventos práticos e mão na massa')

    def test_categoria_str_retorna_nome(self):
        categoria = Categoria.objects.create(nome='Palestra')

        self.assertEqual(str(categoria), 'Palestra')

    def test_categoria_descricao_opcional(self):
        categoria = Categoria.objects.create(nome='Simpósio')

        self.assertIsNone(categoria.descricao)

    def test_categoria_nome_e_unico(self):
        Categoria.objects.create(nome='Congresso')

        with self.assertRaises(Exception):
            Categoria.objects.create(nome='Congresso')

    def test_categoria_meta_ordering_por_nome(self):
        Categoria.objects.create(nome='Zebra')
        Categoria.objects.create(nome='Alfa')
        Categoria.objects.create(nome='Média')

        nomes = list(Categoria.objects.values_list('nome', flat=True))
        self.assertEqual(nomes, ['Alfa', 'Média', 'Zebra'])
