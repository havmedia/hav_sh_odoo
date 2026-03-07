from odoo.tests.common import TransactionCase


class HavShBaseCase(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.server = cls.env['havsh.server'].create({
            'name': 'Test Server',
            'uuid': 'test-server-uuid',
            'external_id': 'srv-1',
            'is_ready_for_odoo': True,
        })
        cls.env.company.write({
            'hav_sh_webhook_token': 'test-webhook-token',
            'hav_sh_api_token': 'test-api-token',
            'hav_sh_api_host': 'https://test.hav.sh',
        })

    def _make_webhook_odoo_data(self, **overrides):
        data = {
            'uuid': 'odoo-uuid-1',
            'id': 'odoo-ext-1',
            'name': 'Webhook Odoo',
            'slug': 'webhook-odoo',
            'description': 'Test description',
            'is_running': True,
            'version': '18.0',
            'type': 'demo',
            'server_id': 'srv-1',
            'initial_modules': ['sale', 'purchase'],
            'hostnames': ['test.example.com'],
            'admin_user': 'admin',
            'created_at': '2025-01-01T00:00:00.000000Z',
            'updated_at': '2025-01-01T12:00:00.000000Z',
        }
        data.update(overrides)
        return data

    def _make_webhook_server_data(self, **overrides):
        data = {
            'uuid': 'new-server-uuid',
            'id': 'srv-new',
            'name': 'Webhook Server',
            'description': 'A test server',
            'ip': '10.0.0.1',
            'port': 22,
            'user': 'root',
            'private_key_id': 'key-1',
            'is_reachable': True,
            'is_docker_installed': True,
            'database_postgres': True,
            'database_postgres_running': True,
            'proxy_traefik': True,
            'proxy_traefik_running': True,
            'proxy_traefik_acme_mail': 'admin@test.com',
            'monitoring_beszel': False,
            'monitoring_beszel_running': False,
            'is_ready_for_odoo': True,
            'created_at': '2025-01-01T00:00:00.000000Z',
            'updated_at': '2025-01-01T12:00:00.000000Z',
        }
        data.update(overrides)
        return data
