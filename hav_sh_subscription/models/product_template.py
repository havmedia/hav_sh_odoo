from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    havsh_provisioning_template_id = fields.Many2one(
        'havsh.provisioning.template',
        string='HAV.sh Provisioning Template',
    )
