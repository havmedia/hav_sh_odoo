from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import ValidationError
import datetime
import re
from slugify import slugify

DATETIME_FORMAT = '%Y-%m-%dT%H:%M:%S.%fZ'


class HavShOdoo(models.Model):
    _name = 'havsh.odoo'
    _description = 'Odoo'
    _inherit = ['mail.thread']

    _sql_constraints = [
        ('uuid_unique',
         'unique(uuid)',
         'The uuid must be unique.'),
    ]

    active = fields.Boolean('Active', default=True)
    state = fields.Selection(
        selection=[
            ('draft', 'Draft'),
            ('creation_requested', 'Creation Requested'),
            ('running', 'Running'),
            ('deletion_requested', 'Deletion Requested'),
            ('deleted', 'Deleted'),
        ],
        string='Status',
        default='draft',
        tracking=True,
    )

    uuid = fields.Char(readonly=True)
    external_id = fields.Char(readonly=True)
    name = fields.Char(string='Name', required=True)
    slug = fields.Char(string='Slug', readonly=True)
    description = fields.Text(string='Description')
    is_running = fields.Boolean(string='Is Running', readonly=True, tracking=True)
    version = fields.Selection(
        string='Version',
        required=True,
        selection=[('18.0', '18.0'), ('19.0', '19.0'), ('20.0', '20.0')]
    )
    admin_user = fields.Char(string='Admin User')
    initial_module_ids = fields.One2many('havsh.odoo.module', 'odoo_id', string='Initial Modules')
    hostname_ids = fields.One2many('havsh.odoo.hostname', 'odoo_id', string='Hostnames')
    first_hostname = fields.Char(string='First Hostname', compute='_compute_first_hostname')
    hostname_count = fields.Integer(string='Hostname Count', compute='_compute_first_hostname')
    type = fields.Selection(
        string='Type',
        selection=[('demo', 'Demo')],
        selection_add=[
            ('test', 'Test'),
            ('live', 'Live'),
            ('copy', 'Copy'),
            ('preview', 'Preview'),
        ],
        required=True,
    )
    odoo_created_at = fields.Datetime(string='Created At', readonly=True)
    odoo_updated_at = fields.Datetime(string='Updated At', readonly=True)
    odoo_deleted_at = fields.Datetime(string='Deleted At', readonly=True)

    server_id = fields.Many2one(
        'havsh.server',
        string='Server',
        domain=[('is_ready_for_odoo', '=', True)],
        required=True
    )

    res_model = fields.Char('Resource Model', compute="_compute_res_record", recursive=True, store=True)
    res_id = fields.Many2oneReference('Resource ID', compute="_compute_res_record", recursive=True, store=True,
                                      model_field="res_model")
    res_name = fields.Char('Resource Name', compute="_compute_res_name", compute_sudo=True)

    @api.depends('res_model', 'res_id')
    def _compute_res_name(self):
        for record in self:
            if record.res_id and record.res_model:
                record.res_name = self.env[record.res_model].browse(record.res_id).display_name
            else:
                record.res_name = False

    @api.depends('hostname_ids')
    def _compute_first_hostname(self):
        for record in self:
            record.hostname_count = len(record.hostname_ids)
            record.first_hostname = record.hostname_ids[0].name if record.hostname_ids else False

    def action_open_hostname(self):
        self.ensure_one()
        if self.first_hostname:
            return {
                'type': 'ir.actions.act_url',
                'url': f'https://{self.first_hostname}',
                'target': 'new',
            }

    # -------------------------------------------------------------------------
    # Helper method to avoid duplication
    # -------------------------------------------------------------------------
    def _prepare_vals_from_data(self, data):
        """Convert incoming webhook/payload data into model-compatible vals."""
        server_id = False
        if data.get('server_id'):
            server = self.env['havsh.server'].search(
                [('external_id', '=', data['server_id'])], limit=1
            )
            server_id = server.id if server else False

        initial_module_vals = []
        if data.get('initial_modules'):
            initial_module_vals.append((5, 0, 0))
            for module_name in data['initial_modules']:
                initial_module_vals.append((0, 0, {'name': module_name}))

        hostname_vals = []
        if data.get('hostnames'):
            hostname_vals.append((5, 0, 0))
            for hostname in data['hostnames']:
                hostname_vals.append((0, 0, {'name': hostname}))

        return {
            'name': data.get('name'),
            'uuid': data.get('uuid'),
            'slug': data.get('slug'),
            'server_id': server_id,
            'external_id': data.get('id'),
            'description': data.get('description'),
            'is_running': data.get('is_running'),
            'version': data.get('version'),
            'initial_module_ids': initial_module_vals,
            'hostname_ids': hostname_vals,
            'admin_user': data.get('admin_user'),
            'type': data.get('type'),
            'state': 'running' if data.get('uuid') and not data.get('deleted_at') else self.state,
            'odoo_created_at': datetime.datetime.strptime(
                data['created_at'], DATETIME_FORMAT
            ) if data.get('created_at') else False,
            'odoo_updated_at': datetime.datetime.strptime(
                data['updated_at'], DATETIME_FORMAT
            ) if data.get('updated_at') else False,
        }

    # -------------------------------------------------------------------------
    # CRUD from webhook
    # -------------------------------------------------------------------------
    @api.model
    def create_from_webhook(self, data):
        record = self.search(
            [('uuid', '=', data['uuid']), ('active', 'in', [True, False])],
            limit=1,
        )
        if record:
            self.update_from_webhook(data)
            return

        vals = self._prepare_vals_from_data(data)
        record = self.with_user(SUPERUSER_ID).sudo().create(vals)
        record.message_post(body=_("Instance created in HAV.sh"))

    @api.model
    def update_from_webhook(self, data):
        record = self.search(
            [('uuid', '=', data['uuid']), ('active', 'in', [True, False])],
            limit=1,
        )
        if not record:
            self.create_from_webhook(data)
            return

        old_state = record.state
        vals = record._prepare_vals_from_data(data)
        record.with_user(SUPERUSER_ID).sudo().write(vals)
        if old_state in ['draft', 'creation_requested'] and record.state == 'running':
            record.message_post(body=_("Instance created in HAV.sh"))

    @api.model
    def delete_from_webhook(self, data):
        record = self.search(
            [('uuid', '=', data['uuid']), ('active', 'in', [True, False])],
            limit=1,
        )
        if record:
            record.with_user(SUPERUSER_ID).sudo().write({
                'active': False,
                'state': 'deleted',
                'odoo_deleted_at': datetime.datetime.strptime(
                    data['deleted_at'], DATETIME_FORMAT
                ) if data.get('deleted_at') else False,
            })
            record.message_post(body=_("Instance deleted from HAV.sh"))

    # -------------------------------------------------------------------------
    # Create HavSh from Odoo
    # -------------------------------------------------------------------------
    def create_hav_sh(self):
        self.ensure_one()
        if self.state != 'draft':
            raise ValidationError(_("Can only create instances in 'Draft' state."))
        payload = {
            'name': self.name,
            'description': self.description or None,
            'version': self.version,
            'initial_modules': self.initial_module_ids.mapped('name'),
            'type': self.type,
            'server_id': self.server_id.external_id,
        }
        try:
            data = self.env.company.call_hav_sh('service-odoo', payload=payload, method='POST')
            self.message_post(body=_("Creation request transmitted to HAV.sh"))
            self.sudo().write({'state': 'creation_requested'})
        except Exception as e:
            msg = _("Failed to create Odoo in HAV.sh: %s") % e
            self.sudo().message_post(body=msg)
            raise ValidationError(msg)

        vals = self._prepare_vals_from_data(data['data'])
        self.sudo().write(vals)

    # -------------------------------------------------------------------------
    # Update from API
    # -------------------------------------------------------------------------
    def action_update_from_api(self):
        for record in self:
            if not record.external_id:
                record.message_post(body=_("Cannot update: no external ID found."))
                continue
            try:
                response = self.env.company.call_hav_sh(f'service-odoo/{record.external_id}', method='GET')
                data = response.get('data', response)
                vals = record._prepare_vals_from_data(data)
                record.write(vals)
                record.message_post(body=_("Instance updated from HAV.sh API"))
            except Exception as e:
                record.message_post(body=_("Failed to update from HAV.sh API: %s") % e)

    # -------------------------------------------------------------------------
    # Deletion Flow
    # -------------------------------------------------------------------------
    def action_delete(self):
        self.ensure_one()
        if self.state != 'running':
            raise ValidationError(_("Can only delete instances in 'Running' state."))

        try:
            self.env.company.call_hav_sh(f'service-odoo/{self.external_id}', method='DELETE')
            self.message_post(body=_("Deletion request transmitted to HAV.sh"))
            self.sudo().write({'state': 'deletion_requested'})
        except Exception as e:
            msg = _("Failed to delete Odoo in HAV.sh: %s") % e
            self.message_post(body=msg)
            raise ValidationError(msg)

    # -------------------------------------------------------------------------
    # Stop / Start
    # -------------------------------------------------------------------------
    def _havsh_stop(self):
        self.ensure_one()
        if not self.external_id:
            return
        try:
            self.env.company.call_hav_sh(
                f'service-odoo/{self.external_id}/stop',
                method='POST',
            )
            self.message_post(body=_("Stop request transmitted to HAV.sh"))
        except Exception as e:
            self.message_post(body=_("Failed to stop instance: %s") % e)
            raise

    def _havsh_start(self):
        self.ensure_one()
        if not self.external_id:
            return
        try:
            self.env.company.call_hav_sh(
                f'service-odoo/{self.external_id}/start',
                method='POST',
            )
            self.message_post(body=_("Start request transmitted to HAV.sh"))
        except Exception as e:
            self.message_post(body=_("Failed to start instance: %s") % e)
            raise