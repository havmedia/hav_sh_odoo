from odoo.tests import tagged

from .common import HavShBaseCase


@tagged('post_install', '-at_install')
class TestHavShHostname(HavShBaseCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.odoo_instance = cls.env['havsh.odoo'].create({
            'name': 'Hostname Test Instance',
            'version': '18.0',
            'type': 'demo',
            'server_id': cls.server.id,
        })

    def test_action_open_hostname(self):
        hostname = self.env['havsh.odoo.hostname'].create({
            'odoo_id': self.odoo_instance.id,
            'name': 'demo.example.com',
        })
        action = hostname.action_open_hostname()
        self.assertEqual(action['type'], 'ir.actions.act_url')
        self.assertEqual(action['url'], 'https://demo.example.com')
        self.assertEqual(action['target'], 'new')

    def test_cascade_delete(self):
        hostname = self.env['havsh.odoo.hostname'].create({
            'odoo_id': self.odoo_instance.id,
            'name': 'cascade.example.com',
        })
        hostname_id = hostname.id
        self.odoo_instance.unlink()
        remaining = self.env['havsh.odoo.hostname'].search([('id', '=', hostname_id)])
        self.assertFalse(remaining)
