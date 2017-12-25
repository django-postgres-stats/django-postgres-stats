from django.conf.urls import include, url as path
from django.contrib import admin
from django.contrib.auth.models import User
from django.test import TestCase, override_settings

urlpatterns = [
    path('^postgres-metrics/', include('postgres_metrics.urls')),
    path('^admin/', admin.site.urls),
]


@override_settings(ROOT_URLCONF=__name__)
class TestMetricsView(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user('user', 'user@local')
        cls.admin = User.objects.create_superuser('admin', 'admin@local', 'secret')

    def test_unauthenticated(self):
        result = self.client.get('/postgres-metrics/aname/')
        self.assertEqual(403, result.status_code)

    def test_not_super(self):
        self.client.force_login(self.user)
        result = self.client.get('/postgres-metrics/aname/')
        self.assertEqual(403, result.status_code)

    def test_permitted_no_metric(self):
        self.client.force_login(self.admin)
        result = self.client.get('/postgres-metrics/')
        self.assertEqual(404, result.status_code)

    def test_permitted_invalid_metric(self):
        self.client.force_login(self.admin)
        result = self.client.get('/postgres-metrics/NOT_A_METRIC/')
        self.assertEqual(404, result.status_code)

    def test_permitted_metric(self):
        self.client.force_login(self.admin)
        result = self.client.get('/postgres-metrics/cache-hits/')
        self.assertEqual(200, result.status_code)
        result = self.client.get('/postgres-metrics/index-usage/')
        self.assertEqual(200, result.status_code)

    def test_metric_results(self):
        self.client.force_login(self.admin)
        result = self.client.get('/postgres-metrics/cache-hits/')
        self.assertEqual(2, len(result.context['results']))
        metric = result.context['metric']
        self.assertEqual(
            ['heap read', 'heap hit', 'ratio'],
            [str(h) for h in metric.headers],
        )

    def test_detail_view_sidebar(self):
        self.client.force_login(self.admin)
        result = self.client.get('/postgres-metrics/index-size/')
        self.assertContains(
            result,
            '<h2>PostgreSQL Metrics</h2>',
            html=True,
        )
        self.assertInHTML(
            '<li><a href="/postgres-metrics/available-extensions/" '
            'title="Available Extensions">Available Extensions</a></li>',
            result.content.decode(),
        )
        self.assertInHTML(
            '<li class="selected"><a href="/postgres-metrics/index-size/" '
            'title="Index Size">Index Size</a></li>',
            result.content.decode(),
        )

    def test_admin_index_list(self):
        self.client.force_login(self.admin)
        result = self.client.get('/admin/')
        self.assertContains(
            result,
            '<th scope="row"><a href="/postgres-metrics/cache-hits/" title="Cache Hits">Cache Hits</a></th>',
            html=True,
        )
        self.assertContains(
            result,
            '<th scope="row"><a href="/postgres-metrics/index-usage/" title="Index Usage">Index Usage</a></th>',
            html=True,
        )
