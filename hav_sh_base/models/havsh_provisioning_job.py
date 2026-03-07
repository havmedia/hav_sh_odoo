import datetime
import logging

from odoo import api, fields, models, _

_logger = logging.getLogger(__name__)

DATETIME_FORMAT = '%Y-%m-%dT%H:%M:%S.%fZ'


class HavShProvisioningJob(models.Model):
    _name = 'havsh.provisioning.job'
    _description = 'Provisioning Job'
    _inherit = ['mail.thread']

    _sql_constraints = [
        ('external_id_unique',
         'unique(external_id)',
         'The external_id must be unique.'),
    ]

    name = fields.Char(string='Customer Name', required=True, readonly=True)
    state = fields.Selection(
        selection=[
            ('pending', 'Pending'),
            ('ordering_server', 'Ordering Server'),
            ('installing_docker', 'Installing Docker'),
            ('configuring_database', 'Configuring Database'),
            ('configuring_proxy', 'Configuring Proxy'),
            ('configuring_monitoring', 'Configuring Monitoring'),
            ('creating_odoo', 'Creating Odoo'),
            ('completed', 'Completed'),
            ('failed', 'Failed'),
        ],
        string='Status',
        default='pending',
        tracking=True,
    )
    external_id = fields.Integer(string='External ID', readonly=True)
    uuid = fields.Char(string='UUID', readonly=True)
    provisioning_template_id = fields.Many2one(
        'havsh.provisioning.template',
        string='Provisioning Template',
        required=True,
        readonly=True,
    )
    res_model = fields.Char(string='Resource Model')
    res_id = fields.Many2oneReference(
        string='Resource ID',
        model_field='res_model',
    )
    havsh_odoo_id = fields.Many2one('havsh.odoo', string='HAV.sh Odoo', readonly=True)
    last_error = fields.Text(string='Last Error', readonly=True)
    server_external_id = fields.Integer(string='Server External ID', readonly=True)
    service_odoo_external_id = fields.Integer(string='Service Odoo External ID', readonly=True)
    started_at = fields.Datetime(string='Started At', readonly=True)
    completed_at = fields.Datetime(string='Completed At', readonly=True)

    def _execute_provisioning(self):
        self.ensure_one()
        template = self.provisioning_template_id
        payload = {'customer_name': self.name}
        try:
            response = self.env.company.call_hav_sh(
                f'provisioning-templates/{template.external_id}/provision',
                payload=payload,
                method='POST',
            )
            data = response.get('data', response)
            vals = self._update_from_api_data(data)
            self.sudo().write(vals)
            self.message_post(body=_("Provisioning request submitted to HAV.sh"))
        except Exception as e:
            self.sudo().write({
                'state': 'failed',
                'last_error': str(e),
            })
            self.message_post(body=_("Provisioning failed: %s") % e)
            raise

    def _update_from_api_data(self, data):
        vals = {}
        if data.get('id'):
            vals['external_id'] = data['id']
        if data.get('uuid'):
            vals['uuid'] = data['uuid']
        if data.get('status'):
            vals['state'] = data['status']
        if data.get('server_id'):
            vals['server_external_id'] = data['server_id']
        if data.get('service_odoo_id'):
            vals['service_odoo_external_id'] = data['service_odoo_id']
        if data.get('last_error'):
            vals['last_error'] = data['last_error']
        if data.get('started_at'):
            vals['started_at'] = datetime.datetime.strptime(
                data['started_at'], DATETIME_FORMAT
            )
        if data.get('completed_at'):
            vals['completed_at'] = datetime.datetime.strptime(
                data['completed_at'], DATETIME_FORMAT
            )
        return vals

    def action_poll_status(self):
        for record in self:
            if not record.external_id:
                continue
            try:
                response = self.env.company.call_hav_sh(
                    f'provisionings/{record.external_id}',
                    method='GET',
                )
                data = response.get('data', response)
                vals = record._update_from_api_data(data)
                record.sudo().write(vals)

                if record.state == 'completed':
                    record._on_provisioning_completed()
                elif record.state == 'failed':
                    record._on_provisioning_failed()
            except Exception as e:
                record.message_post(body=_("Failed to poll status: %s") % e)

    def _on_provisioning_completed(self):
        self.ensure_one()
        if self.havsh_odoo_id:
            return
        if not self.service_odoo_external_id:
            return
        odoo_record = self.env['havsh.odoo'].search(
            [('external_id', '=', str(self.service_odoo_external_id))],
            limit=1,
        )
        if odoo_record:
            self.sudo().write({'havsh_odoo_id': odoo_record.id})
            odoo_record.sudo().write({
                'res_model': self.res_model,
                'res_id': self.res_id,
            })
            self.message_post(body=_("Linked to HAV.sh Odoo instance: %s") % odoo_record.name)

    def _on_provisioning_failed(self):
        self.ensure_one()
        self.message_post(body=_("Provisioning failed: %s") % (self.last_error or 'Unknown error'))

    @api.model
    def cron_poll_provisioning_status(self):
        jobs = self.search([
            ('state', 'not in', ['completed', 'failed']),
            ('external_id', '!=', 0),
        ])
        jobs.action_poll_status()

        # Retry linking for completed jobs that don't have havsh_odoo_id yet
        unlinked = self.search([
            ('state', '=', 'completed'),
            ('havsh_odoo_id', '=', False),
            ('service_odoo_external_id', '!=', 0),
        ])
        for job in unlinked:
            job._on_provisioning_completed()
