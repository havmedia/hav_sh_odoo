from odoo import api, fields, models


class CrmLead(models.Model):
    _inherit = 'crm.lead'

    havsh_odoo_ids = fields.One2many('havsh.odoo', 'res_id')

    havsh_odoo_system_count = fields.Integer(compute='_compute_hav_odoo_system_count')

    @api.depends('havsh_odoo_ids')
    def _compute_hav_odoo_system_count(self):
        for crm in self:
            crm.havsh_odoo_system_count = len(crm.havsh_odoo_ids)

    def action_show_havsh_odoo_systems(self):
        self.ensure_one()

        action = self.env["ir.actions.actions"]._for_xml_id("hav_sh_base.action_havsh_odoos")
        action['domain'] = [('res_id', '=', self.id), ('res_model', '=', self._name)]
        action['context'] = {
            'default_name': self.name,
            'default_res_model': self._name,
            'default_res_id': self.id,
            'default_type': 'demo',
            'default_version': '19.0',
            'description': f'This is a demo system created in Odoo for the deal id {self.id}',
        }
        return action
