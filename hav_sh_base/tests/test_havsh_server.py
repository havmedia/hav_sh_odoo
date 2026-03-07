from odoo.tests import tagged

from .common import HavShBaseCase


@tagged('post_install', '-at_install')
class TestHavShServer(HavShBaseCase):

    # ------------------------------------------------------------------
    # _prepare_vals_from_data
    # ------------------------------------------------------------------
    def test_prepare_vals_from_data(self):
        data = self._make_webhook_server_data()
        vals = self.server._prepare_vals_from_data(data)

        self.assertTrue(vals['active'])
        self.assertEqual(vals['name'], 'Webhook Server')
        self.assertEqual(vals['uuid'], 'new-server-uuid')
        self.assertEqual(vals['external_id'], 'srv-new')
        self.assertEqual(vals['ip'], '10.0.0.1')
        self.assertEqual(vals['port'], 22)
        self.assertEqual(vals['user'], 'root')
        self.assertTrue(vals['is_reachable'])
        self.assertTrue(vals['is_docker_installed'])
        self.assertTrue(vals['is_ready_for_odoo'])
        self.assertTrue(vals['database_postgres'])
        self.assertTrue(vals['database_postgres_running'])
        self.assertTrue(vals['proxy_traefik'])
        self.assertTrue(vals['proxy_traefik_running'])
        self.assertFalse(vals['monitoring_beszel'])
        self.assertFalse(vals['monitoring_beszel_running'])
        self.assertTrue(vals['odoo_created_at'])
        self.assertTrue(vals['odoo_updated_at'])

    def test_prepare_vals_from_data_no_timestamps(self):
        data = self._make_webhook_server_data(created_at=None, updated_at=None)
        del data['created_at']
        del data['updated_at']
        vals = self.server._prepare_vals_from_data(data)
        self.assertFalse(vals['odoo_created_at'])
        self.assertFalse(vals['odoo_updated_at'])

    # ------------------------------------------------------------------
    # Webhook CRUD
    # ------------------------------------------------------------------
    def test_create_from_webhook_new(self):
        data = self._make_webhook_server_data()
        self.env['havsh.server'].create_from_webhook(data)
        record = self.env['havsh.server'].search([('uuid', '=', 'new-server-uuid')])
        self.assertTrue(record)
        self.assertEqual(record.name, 'Webhook Server')
        self.assertEqual(record.ip, '10.0.0.1')

    def test_create_from_webhook_existing_updates(self):
        data = self._make_webhook_server_data(uuid='test-server-uuid')
        data['name'] = 'Updated Server'
        self.env['havsh.server'].create_from_webhook(data)
        self.server.invalidate_recordset()
        self.assertEqual(self.server.name, 'Updated Server')

    def test_update_from_webhook_existing(self):
        data = self._make_webhook_server_data(uuid='test-server-uuid')
        data['ip'] = '192.168.1.1'
        self.env['havsh.server'].update_from_webhook(data)
        self.server.invalidate_recordset()
        self.assertEqual(self.server.ip, '192.168.1.1')

    def test_update_from_webhook_missing_creates(self):
        data = self._make_webhook_server_data(uuid='update-creates-srv')
        self.env['havsh.server'].update_from_webhook(data)
        record = self.env['havsh.server'].search([('uuid', '=', 'update-creates-srv')])
        self.assertTrue(record)

    def test_delete_from_webhook(self):
        data = self._make_webhook_server_data()
        self.env['havsh.server'].create_from_webhook(data)
        delete_data = {
            'uuid': 'new-server-uuid',
            'deleted_at': '2025-06-01T00:00:00.000000Z',
        }
        self.env['havsh.server'].delete_from_webhook(delete_data)
        record = self.env['havsh.server'].search([
            ('uuid', '=', 'new-server-uuid'),
            ('active', 'in', [True, False]),
        ])
        self.assertFalse(record.active)
        self.assertTrue(record.odoo_deleted_at)

    def test_delete_from_webhook_missing_does_nothing(self):
        delete_data = {
            'uuid': 'nonexistent-uuid',
            'deleted_at': '2025-06-01T00:00:00.000000Z',
        }
        # Should not raise
        self.env['havsh.server'].delete_from_webhook(delete_data)

    def test_delete_from_webhook_no_deleted_at(self):
        data = self._make_webhook_server_data()
        self.env['havsh.server'].create_from_webhook(data)
        delete_data = {'uuid': 'new-server-uuid'}
        self.env['havsh.server'].delete_from_webhook(delete_data)
        record = self.env['havsh.server'].search([
            ('uuid', '=', 'new-server-uuid'),
            ('active', 'in', [True, False]),
        ])
        self.assertFalse(record.active)
        self.assertFalse(record.odoo_deleted_at)
