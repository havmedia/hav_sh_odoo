from unittest.mock import patch

from odoo.tests.common import TransactionCase


class HavShSubscriptionTestCommon(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.company = cls.env.company
        cls.company.write({
            'hav_sh_api_token': 'test-token',
            'hav_sh_api_host': 'https://test.hav.sh',
        })

        cls.provisioning_template = cls.env['havsh.provisioning.template'].create({
            'external_id': 1,
            'name': 'Test Template',
            'odoo_version': '18.0',
            'odoo_type': 'live',
        })

        cls.product = cls.env['product.template'].create({
            'name': 'HAV.sh Hosting',
            'type': 'service',
            'recurring_invoice': True,
            'havsh_provisioning_template_id': cls.provisioning_template.id,
        })

        cls.partner = cls.env['res.partner'].create({
            'name': 'Test Customer',
        })
