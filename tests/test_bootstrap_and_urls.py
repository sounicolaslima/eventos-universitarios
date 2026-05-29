import builtins
import importlib
from unittest.mock import patch

from django.test import SimpleTestCase, override_settings


class BootstrapAndUrlsTest(SimpleTestCase):
    def test_manage_main_raises_importerror_when_django_import_fails(self):
        import manage

        original_import = builtins.__import__

        def fake_import(name, globals=None, locals=None, fromlist=(), level=0):
            if name == 'django.core.management':
                raise ImportError('forced failure')
            return original_import(name, globals, locals, fromlist, level)

        self.assertIs(fake_import('os'), original_import('os'))

        with patch('builtins.__import__', side_effect=fake_import):
            with self.assertRaises(ImportError):
                manage.main()

    @override_settings(DEBUG=True)
    def test_eventos_urls_add_static_patterns_when_debug(self):
        import eventos.urls as eventos_urls

        before = len(eventos_urls.urlpatterns)
        reloaded = importlib.reload(eventos_urls)
        after = len(reloaded.urlpatterns)

        self.assertGreater(after, before)

    @override_settings(DEBUG=True)
    def test_project_urls_add_static_patterns_when_debug(self):
        import eventos_universitarios.urls as project_urls

        before = len(project_urls.urlpatterns)
        reloaded = importlib.reload(project_urls)
        after = len(reloaded.urlpatterns)

        self.assertGreater(after, before)