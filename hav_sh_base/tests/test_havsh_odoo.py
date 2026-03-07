from unittest.mock import patch

from odoo.exceptions import ValidationError
from odoo.tests import tagged

from .common import HavShBaseCase


@tagged('post_install', '-at_install')
class TestHavShOdoo(HavShBaseCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.odoo_instance = cls.env['havsh.odoo'].create({
            'name': 'Test Instance',
            'version': '18.0',
            'type': 'demo',
            'server_id': cls.server.id,
        })

    # ------------------------------------------------------------------
    # Computed fields
    # ------------------------------------------------------------------
    def test_compute_first_hostname_empty(self):
        self.assertFalse(self.odoo_instance.first_hostname)
        self.assertEqual(self.odoo_instance.hostname_count, 0)

    def test_compute_first_hostname_with_hostnames(self):
        self.env['havsh.odoo.hostname'].create({
            'odoo_id': self.odoo_instance.id,
            'name': 'first.example.com',
        })
        self.env['havsh.odoo.hostname'].create({
            'odoo_id': self.odoo_instance.id,
            'name': 'second.example.com',
        })
        self.assertEqual(self.odoo_instance.first_hostname, 'first.example.com')
        self.assertEqual(self.odoo_instance.hostname_count, 2)

    def test_action_open_hostname(self):
        self.env['havsh.odoo.hostname'].create({
            'odoo_id': self.odoo_instance.id,
            'name': 'test.example.com',
        })
        action = self.odoo_instance.action_open_hostname()
        self.assertEqual(action['type'], 'ir.actions.act_url')
        self.assertEqual(action['url'], 'https://test.example.com')
        self.assertEqual(action['target'], 'new')

    def test_action_open_hostname_no_hostname(self):
        result = self.odoo_instance.action_open_hostname()
        self.assertIsNone(result)

    # ------------------------------------------------------------------
    # _prepare_vals_from_data
    # ------------------------------------------------------------------
    def test_prepare_vals_from_data(self):
        data = self._make_webhook_odoo_data()
        vals = self.odoo_instance._prepare_vals_from_data(data)

        self.assertEqual(vals['name'], 'Webhook Odoo')
        self.assertEqual(vals['uuid'], 'odoo-uuid-1')
        self.assertEqual(vals['slug'], 'webhook-odoo')
        self.assertEqual(vals['server_id'], self.server.id)
        self.assertEqual(vals['external_id'], 'odoo-ext-1')
        self.assertEqual(vals['version'], '18.0')
        self.assertTrue(vals['is_running'])
        self.assertEqual(vals['state'], 'running')
        self.assertEqual(vals['admin_user'], 'admin')
        self.assertEqual(len(vals['initial_module_ids']), 3)  # (5,0,0) + 2 modules
        self.assertEqual(len(vals['hostname_ids']), 2)  # (5,0,0) + 1 hostname

    def test_prepare_vals_from_data_unknown_server(self):
        data = self._make_webhook_odoo_data(server_id='nonexistent')
        vals = self.odoo_instance._prepare_vals_from_data(data)
        self.assertFalse(vals['server_id'])

    def test_prepare_vals_from_data_deleted(self):
        data = self._make_webhook_odoo_data(
            deleted_at='2025-06-01T00:00:00.000000Z',
        )
        vals = self.odoo_instance._prepare_vals_from_data(data)
        # state stays as current instance state when deleted_at is set
        self.assertEqual(vals['state'], self.odoo_instance.state)

    # ------------------------------------------------------------------
    # Webhook CRUD
    # ------------------------------------------------------------------
    def test_create_from_webhook_new(self):
        data = self._make_webhook_odoo_data(uuid='brand-new-uuid')
        self.env['havsh.odoo'].create_from_webhook(data)
        record = self.env['havsh.odoo'].search([('uuid', '=', 'brand-new-uuid')])
        self.assertTrue(record)
        self.assertEqual(record.name, 'Webhook Odoo')
        self.assertEqual(record.state, 'running')

    def test_create_from_webhook_existing_updates(self):
        data = self._make_webhook_odoo_data(uuid='brand-new-uuid')
        self.env['havsh.odoo'].create_from_webhook(data)
        # Second call with same UUID should update, not create duplicate
        data['name'] = 'Updated Name'
        self.env['havsh.odoo'].create_from_webhook(data)
        records = self.env['havsh.odoo'].search([('uuid', '=', 'brand-new-uuid')])
        self.assertEqual(len(records), 1)
        self.assertEqual(records.name, 'Updated Name')

    def test_update_from_webhook_existing(self):
        data = self._make_webhook_odoo_data(uuid='brand-new-uuid')
        self.env['havsh.odoo'].create_from_webhook(data)
        data['name'] = 'Updated via webhook'
        self.env['havsh.odoo'].update_from_webhook(data)
        record = self.env['havsh.odoo'].search([('uuid', '=', 'brand-new-uuid')])
        self.assertEqual(record.name, 'Updated via webhook')

    def test_update_from_webhook_missing_creates(self):
        data = self._make_webhook_odoo_data(uuid='update-creates-uuid')
        self.env['havsh.odoo'].update_from_webhook(data)
        record = self.env['havsh.odoo'].search([('uuid', '=', 'update-creates-uuid')])
        self.assertTrue(record)
        self.assertEqual(record.name, 'Webhook Odoo')

    def test_update_from_webhook_posts_message_on_state_change(self):
        """When state transitions from draft/creation_requested to running, a message is posted."""
        instance = self.env['havsh.odoo'].create({
            'name': 'Draft Instance',
            'version': '18.0',
            'type': 'demo',
            'server_id': self.server.id,
            'state': 'creation_requested',
            'uuid': 'state-change-uuid',
        })
        message_count_before = len(instance.message_ids)
        data = self._make_webhook_odoo_data(uuid='state-change-uuid')
        self.env['havsh.odoo'].update_from_webhook(data)
        instance.invalidate_recordset()
        self.assertGreater(len(instance.message_ids), message_count_before)

    def test_delete_from_webhook(self):
        data = self._make_webhook_odoo_data(uuid='delete-me-uuid')
        self.env['havsh.odoo'].create_from_webhook(data)
        delete_data = {
            'uuid': 'delete-me-uuid',
            'deleted_at': '2025-06-01T00:00:00.000000Z',
        }
        self.env['havsh.odoo'].delete_from_webhook(delete_data)
        record = self.env['havsh.odoo'].search([
            ('uuid', '=', 'delete-me-uuid'),
            ('active', 'in', [True, False]),
        ])
        self.assertFalse(record.active)
        self.assertEqual(record.state, 'deleted')

    def test_delete_from_webhook_missing_does_nothing(self):
        delete_data = {
            'uuid': 'nonexistent-uuid',
            'deleted_at': '2025-06-01T00:00:00.000000Z',
        }
        # Should not raise
        self.env['havsh.odoo'].delete_from_webhook(delete_data)

    # ------------------------------------------------------------------
    # Create HAV.sh (API call)
    # ------------------------------------------------------------------
    def test_create_hav_sh_not_draft_raises(self):
        self.odoo_instance.state = 'running'
        with self.assertRaises(ValidationError):
            self.odoo_instance.create_hav_sh()

    @patch.object(type(HavShBaseCase), '_fake', create=True)
    def test_create_hav_sh_draft(self):
        instance = self.env['havsh.odoo'].create({
            'name': 'New Draft',
            'version': '19.0',
            'type': 'demo',
            'server_id': self.server.id,
        })
        api_response = {
            'data': self._make_webhook_odoo_data(uuid='api-created-uuid'),
        }
        with patch.object(
            type(self.env.company), 'call_hav_sh', return_value=api_response,
        ) as mock_call:
            instance.create_hav_sh()
            mock_call.assert_called_once()
            args = mock_call.call_args
            self.assertEqual(args[0][0], 'service-odoo')
        self.assertEqual(instance.state, 'running')
        self.assertEqual(instance.uuid, 'api-created-uuid')

    def test_create_hav_sh_api_error(self):
        instance = self.env['havsh.odoo'].create({
            'name': 'Will Fail',
            'version': '18.0',
            'type': 'demo',
            'server_id': self.server.id,
        })
        with patch.object(
            type(self.env.company), 'call_hav_sh', side_effect=Exception('API down'),
        ):
            with self.assertRaises(ValidationError):
                instance.create_hav_sh()

    # ------------------------------------------------------------------
    # Update from API
    # ------------------------------------------------------------------
    def test_action_update_from_api_no_external_id(self):
        """Records without external_id post an info message."""
        self.odoo_instance.external_id = False
        message_count_before = len(self.odoo_instance.message_ids)
        self.odoo_instance.action_update_from_api()
        self.odoo_instance.invalidate_recordset()
        self.assertGreater(len(self.odoo_instance.message_ids), message_count_before)

    def test_action_update_from_api(self):
        self.odoo_instance.external_id = 'ext-123'
        api_response = {
            'data': self._make_webhook_odoo_data(uuid='updated-api-uuid'),
        }
        with patch.object(
            type(self.env.company), 'call_hav_sh', return_value=api_response,
        ):
            self.odoo_instance.action_update_from_api()
        self.assertEqual(self.odoo_instance.uuid, 'updated-api-uuid')

    def test_action_update_from_api_error_posts_message(self):
        self.odoo_instance.external_id = 'ext-123'
        message_count_before = len(self.odoo_instance.message_ids)
        with patch.object(
            type(self.env.company), 'call_hav_sh', side_effect=Exception('timeout'),
        ):
            self.odoo_instance.action_update_from_api()
        self.odoo_instance.invalidate_recordset()
        self.assertGreater(len(self.odoo_instance.message_ids), message_count_before)

    # ------------------------------------------------------------------
    # Delete flow
    # ------------------------------------------------------------------
    def test_action_delete_not_running_raises(self):
        self.odoo_instance.state = 'draft'
        with self.assertRaises(ValidationError):
            self.odoo_instance.action_delete()

    def test_action_delete_running(self):
        instance = self.env['havsh.odoo'].create({
            'name': 'Running Instance',
            'version': '18.0',
            'type': 'demo',
            'server_id': self.server.id,
            'state': 'running',
            'external_id': 'ext-del',
        })
        with patch.object(
            type(self.env.company), 'call_hav_sh', return_value={},
        ):
            instance.action_delete()
        self.assertEqual(instance.state, 'deletion_requested')

    def test_action_delete_api_error(self):
        instance = self.env['havsh.odoo'].create({
            'name': 'Running Instance 2',
            'version': '18.0',
            'type': 'demo',
            'server_id': self.server.id,
            'state': 'running',
            'external_id': 'ext-del-2',
        })
        with patch.object(
            type(self.env.company), 'call_hav_sh', side_effect=Exception('fail'),
        ):
            with self.assertRaises(ValidationError):
                instance.action_delete()
        # State should remain running after failure
        self.assertEqual(instance.state, 'running')

    # ------------------------------------------------------------------
    # Default state
    # ------------------------------------------------------------------
    def test_default_state_is_draft(self):
        instance = self.env['havsh.odoo'].create({
            'name': 'Default State',
            'version': '18.0',
            'type': 'demo',
            'server_id': self.server.id,
        })
        self.assertEqual(instance.state, 'draft')
        self.assertTrue(instance.active)
