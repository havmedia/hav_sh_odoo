from odoo import fields, models


class HavShHostname(models.Model):
    _name = 'havsh.odoo.hostname'
    _description = 'HAV.sh Hostname'
    _order = 'id'

    odoo_id = fields.Many2one('havsh.odoo', string='Odoo Instance', ondelete='cascade', required=True)
    name = fields.Char(string='Hostname', required=True)

    def action_open_hostname(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_url',
            'url': f'https://{self.name}',
            'target': 'new',
        }