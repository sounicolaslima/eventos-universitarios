from types import SimpleNamespace

from django.test import TestCase

from eventos.templatetags.user_tags import (
    get_user_badge,
    is_admin,
    is_staff,
    is_superuser,
    user_role_badge,
)


class UserTagsTest(TestCase):
    def test_filters_reagem_ao_estado_do_usuario(self):
        anonimo = SimpleNamespace(is_authenticated=False, is_staff=False, is_superuser=False)
        staff = SimpleNamespace(is_authenticated=True, is_staff=True, is_superuser=False)
        superuser = SimpleNamespace(is_authenticated=True, is_staff=True, is_superuser=True)

        self.assertFalse(is_admin(anonimo))
        self.assertFalse(is_staff(anonimo))
        self.assertFalse(is_superuser(anonimo))

        self.assertTrue(is_admin(staff))
        self.assertTrue(is_staff(staff))
        self.assertFalse(is_superuser(staff))

        self.assertTrue(is_admin(superuser))
        self.assertTrue(is_staff(superuser))
        self.assertTrue(is_superuser(superuser))

    def test_badges_refletem_o_perfil(self):
        anonimo = SimpleNamespace(is_authenticated=False, is_staff=False, is_superuser=False)
        usuario = SimpleNamespace(is_authenticated=True, is_staff=False, is_superuser=False)
        staff = SimpleNamespace(is_authenticated=True, is_staff=True, is_superuser=False)
        superuser = SimpleNamespace(is_authenticated=True, is_staff=True, is_superuser=True)

        self.assertEqual(get_user_badge(anonimo), '')
        self.assertEqual(get_user_badge(usuario), '')
        self.assertIn('Admin', get_user_badge(staff))
        self.assertIn('Super Admin', get_user_badge(superuser))

        self.assertIn('Visitante', user_role_badge(anonimo))
        self.assertIn('Usuário', user_role_badge(usuario))
        self.assertIn('Admin', user_role_badge(staff))
        self.assertIn('Super Admin', user_role_badge(superuser))