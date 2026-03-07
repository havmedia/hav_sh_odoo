from odoo.exceptions import ValidationError
from odoo.tests import tagged

from .common import HavShBaseCase


@tagged('post_install', '-at_install')
class TestHavShModule(HavShBaseCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.odoo_instance = cls.env['havsh.odoo'].create({
            'name': 'Module Test Instance',
            'version': '18.0',
            'type': 'demo',
            'server_id': cls.server.id,
        })

    def test_valid_module_name(self):
        module = self.env['havsh.odoo.module'].create({
            'odoo_id': self.odoo_instance.id,
            'name': 'sale_management',
        })
        self.assertEqual(module.name, 'sale_management')

    def test_valid_module_name_with_dash(self):
        module = self.env['havsh.odoo.module'].create({
            'odoo_id': self.odoo_instance.id,
            'name': 'my-module',
        })
        self.assertEqual(module.name, 'my-module')

    def test_valid_module_name_alphanumeric(self):
        module = self.env['havsh.odoo.module'].create({
            'odoo_id': self.odoo_instance.id,
            'name': 'module123',
        })
        self.assertEqual(module.name, 'module123')

    def test_invalid_module_name_spaces(self):
        with self.assertRaises(ValidationError):
            self.env['havsh.odoo.module'].create({
                'odoo_id': self.odoo_instance.id,
                'name': 'invalid module',
            })

    def test_invalid_module_name_special_chars(self):
        with self.assertRaises(ValidationError):
            self.env['havsh.odoo.module'].create({
                'odoo_id': self.odoo_instance.id,
                'name': 'invalid@module!',
            })

    def test_invalid_module_name_dots(self):
        with self.assertRaises(ValidationError):
            self.env['havsh.odoo.module'].create({
                'odoo_id': self.odoo_instance.id,
                'name': 'module.name',
            })

    def test_unique_per_odoo_instance(self):
        self.env['havsh.odoo.module'].create({
            'odoo_id': self.odoo_instance.id,
            'name': 'sale',
        })
        with self.assertRaises(Exception):
            self.env['havsh.odoo.module'].create({
                'odoo_id': self.odoo_instance.id,
                'name': 'sale',
            })

    def test_same_name_different_instance(self):
        other_instance = self.env['havsh.odoo'].create({
            'name': 'Other Instance',
            'version': '18.0',
            'type': 'demo',
            'server_id': self.server.id,
        })
        self.env['havsh.odoo.module'].create({
            'odoo_id': self.odoo_instance.id,
            'name': 'crm',
        })
        # Same module name on a different instance should be allowed
        module2 = self.env['havsh.odoo.module'].create({
            'odoo_id': other_instance.id,
            'name': 'crm',
        })
        self.assertTrue(module2)
