from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
import re

class HavShModule(models.Model):
    _name = 'havsh.odoo.module'
    _description = 'HAV.sh Module'
    _order = 'name'

    odoo_id = fields.Many2one('havsh.odoo', string='Odoo Instance', ondelete='cascade', required=True)
    name = fields.Char(string='Name', required=True)

    _sql_constraints = [
        ('name_odoo_unique', 'unique(name, odoo_id)', 'The module name must be unique per Odoo instance!'),
    ]

    @api.constrains('name')
    def _check_name(self):
        for record in self:
            if not re.match(r'^[a-zA-Z0-9_-]+$', record.name):
                raise ValidationError(
                    _("Module name '%s' is invalid. Only alphanumeric characters, dashes, and underscores are allowed.")
                    % record.name
                )
