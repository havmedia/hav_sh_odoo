from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestCrmLead(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.server = cls.env['havsh.server'].create({
            'name': 'Test Server',
            'uuid': 'crm-test-server-uuid',
            'external_id': 'srv-crm',
            'is_ready_for_odoo': True,
        })
        cls.lead = cls.env['crm.lead'].create({
            'name': 'Test Deal',
        })

    def _create_odoo_for_lead(self, name='Demo System', **kwargs):
        vals = {
            'name': name,
            'version': '18.0',
            'type': 'demo',
            'server_id': self.server.id,
        }
        vals.update(kwargs)
        record = self.env['havsh.odoo'].create(vals)
        record.write({
            'res_model': 'crm.lead',
            'res_id': self.lead.id,
        })
        return record

    # ------------------------------------------------------------------
    # Computed count
    # ------------------------------------------------------------------
    def test_system_count_zero(self):
        self.assertEqual(self.lead.havsh_odoo_system_count, 0)

    def test_system_count_one(self):
        self._create_odoo_for_lead()
        self.lead.invalidate_recordset()
        self.assertEqual(self.lead.havsh_odoo_system_count, 1)

    def test_system_count_multiple(self):
        self._create_odoo_for_lead(name='System 1')
        self._create_odoo_for_lead(name='System 2')
        self._create_odoo_for_lead(name='System 3')
        self.lead.invalidate_recordset()
        self.assertEqual(self.lead.havsh_odoo_system_count, 3)

    def test_odoo_ids_relationship(self):
        odoo = self._create_odoo_for_lead()
        self.lead.invalidate_recordset()
        self.assertIn(odoo, self.lead.havsh_odoo_ids)

    # ------------------------------------------------------------------
    # Action
    # ------------------------------------------------------------------
    def test_action_show_havsh_odoo_systems(self):
        action = self.lead.action_show_havsh_odoo_systems()
        self.assertEqual(action['domain'], [
            ('res_id', '=', self.lead.id),
            ('res_model', '=', 'crm.lead'),
        ])
        ctx = action['context']
        self.assertEqual(ctx['default_name'], 'Test Deal')
        self.assertEqual(ctx['default_res_model'], 'crm.lead')
        self.assertEqual(ctx['default_res_id'], self.lead.id)
        self.assertEqual(ctx['default_type'], 'demo')
        self.assertEqual(ctx['default_version'], '20.0')
        self.assertIn(str(self.lead.id), ctx['description'])
