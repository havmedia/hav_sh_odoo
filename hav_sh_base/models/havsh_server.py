import datetime
from odoo import api, fields, models, SUPERUSER_ID

DATETIME_FORMAT = '%Y-%m-%dT%H:%M:%S.%fZ'


class HavShServer(models.Model):
    _name = 'havsh.server'
    _description = 'Server'
    _inherit = ['mail.thread']

    _sql_constraints = [
        ('uuid_unique', 'unique(uuid)', 'The uuid must be unique.'),
    ]

    active = fields.Boolean('Active', default=True)

    uuid = fields.Char(readonly=True)
    external_id = fields.Char(readonly=True)

    name = fields.Char(string='Name')
    description = fields.Text(string='Description')
    ip = fields.Char(string='IP')
    port = fields.Integer(string='Port')
    user = fields.Char(string='User')
    private_key_id = fields.Char(string='Private Key ID')

    is_reachable = fields.Boolean('Reachable')
    is_docker_installed = fields.Boolean('Docker Installed')
    database_postgres = fields.Boolean('Database Postgres')
    database_postgres_running = fields.Boolean('Database Postgres Running')
    proxy_traefik = fields.Boolean('Proxy Traefik')
    proxy_traefik_running = fields.Boolean('Proxy Traefik Running')
    proxy_traefik_acme_mail = fields.Char('Proxy Traefik Acme Mail')
    monitoring_beszel = fields.Boolean('Monitoring BESZEL')
    monitoring_beszel_running = fields.Boolean('Monitoring BESZEL Running')

    is_ready_for_odoo = fields.Boolean('Ready for Odoo')

    odoo_created_at = fields.Datetime(string='Created At', readonly=True)
    odoo_updated_at = fields.Datetime(string='Updated At', readonly=True)
    odoo_deleted_at = fields.Datetime(string='Deleted At', readonly=True)

    # -------------------------------------------------------------------------
    # Helper Method
    # -------------------------------------------------------------------------
    def _prepare_vals_from_data(self, data):
        """Convert webhook/payload data dict to ORM-compatible vals."""
        return {
            'active': True,
            'name': data.get('name'),
            'uuid': data.get('uuid'),
            'external_id': data.get('id'),
            'description': data.get('description'),
            'ip': data.get('ip'),
            'port': data.get('port'),
            'user': data.get('user'),
            'private_key_id': data.get('private_key_id'),
            'is_reachable': data.get('is_reachable'),
            'is_docker_installed': data.get('is_docker_installed'),
            'database_postgres': data.get('database_postgres'),
            'database_postgres_running': data.get('database_postgres_running'),
            'proxy_traefik': data.get('proxy_traefik'),
            'proxy_traefik_running': data.get('proxy_traefik_running'),
            'proxy_traefik_acme_mail': data.get('proxy_traefik_acme_mail'),
            'monitoring_beszel': data.get('monitoring_beszel'),
            'monitoring_beszel_running': data.get('monitoring_beszel_running'),
            'is_ready_for_odoo': data.get('is_ready_for_odoo'),
            'odoo_created_at': datetime.datetime.strptime(
                data['created_at'], DATETIME_FORMAT
            )
            if data.get('created_at')
            else False,
            'odoo_updated_at': datetime.datetime.strptime(
                data['updated_at'], DATETIME_FORMAT
            )
            if data.get('updated_at')
            else False,
        }

    # -------------------------------------------------------------------------
    # Webhook Methods
    # -------------------------------------------------------------------------
    @api.model
    def create_from_webhook(self, data):
        vals = self._prepare_vals_from_data(data)
        record = self.search(
            [('uuid', '=', data.get('uuid')), ('active', 'in', [True, False])],
            limit=1,
        )

        if record:
            record.with_user(SUPERUSER_ID).sudo().write(vals)
        else:
            self.with_user(SUPERUSER_ID).sudo().create(vals)

    @api.model
    def update_from_webhook(self, data):
        vals = self._prepare_vals_from_data(data)
        record = self.search(
            [('uuid', '=', data.get('uuid')), ('active', 'in', [True, False])],
            limit=1,
        )
        if record:
            record.with_user(SUPERUSER_ID).sudo().write(vals)
        else:
            self.with_user(SUPERUSER_ID).sudo().create(vals)

    @api.model
    def delete_from_webhook(self, data):
        record = self.search(
            [('uuid', '=', data.get('uuid')), ('active', 'in', [True, False])],
            limit=1,
        )
        if record:
            record.with_user(SUPERUSER_ID).sudo().write({
                'active': False,
                'odoo_deleted_at': datetime.datetime.strptime(
                    data['deleted_at'], DATETIME_FORMAT
                )
                if data.get('deleted_at')
                else False,
            })