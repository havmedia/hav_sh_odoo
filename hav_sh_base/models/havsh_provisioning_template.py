import datetime

from odoo import api, fields, models, _

DATETIME_FORMAT = '%Y-%m-%dT%H:%M:%S.%fZ'


class HavShProvisioningTemplate(models.Model):
    _name = 'havsh.provisioning.template'
    _description = 'Provisioning Template'

    _sql_constraints = [
        ('external_id_unique',
         'unique(external_id)',
         'The external_id must be unique.'),
    ]

    external_id = fields.Integer(string='External ID', required=True)
    uuid = fields.Char(string='UUID')
    name = fields.Char(string='Name', required=True)
    description = fields.Text(string='Description')
    odoo_version = fields.Selection(
        string='Odoo Version',
        selection=[('18.0', '18.0'), ('19.0', '19.0')],
    )
    odoo_type = fields.Selection(
        string='Odoo Type',
        selection=[
            ('test', 'Test'),
            ('live', 'Live'),
            ('demo', 'Demo'),
            ('copy', 'Copy'),
            ('preview', 'Preview'),
        ],
    )
    cloud_location = fields.Char(string='Cloud Location')
    cloud_server_type = fields.Char(string='Cloud Server Type')
    last_synced_at = fields.Datetime(string='Last Synced At', readonly=True)

    @api.model
    def action_sync_templates(self):
        response = self.env.company.call_hav_sh('provisioning-templates', method='GET')
        templates = response.get('data', response)
        if not isinstance(templates, list):
            templates = [templates]
        for tpl_data in templates:
            ext_id = tpl_data.get('id')
            if not ext_id:
                continue
            record = self.search([('external_id', '=', ext_id)], limit=1)
            vals = {
                'external_id': ext_id,
                'uuid': tpl_data.get('uuid'),
                'name': tpl_data.get('name', ''),
                'description': tpl_data.get('description'),
                'odoo_version': tpl_data.get('odoo_version'),
                'odoo_type': tpl_data.get('odoo_type'),
                'cloud_location': tpl_data.get('cloud_location'),
                'cloud_server_type': tpl_data.get('cloud_server_type'),
                'last_synced_at': fields.Datetime.now(),
            }
            if record:
                record.write(vals)
            else:
                self.create(vals)
