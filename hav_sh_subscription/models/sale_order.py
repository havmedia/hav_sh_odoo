from odoo import api, fields, models, _


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    havsh_odoo_ids = fields.One2many(
        'havsh.odoo',
        'res_id',
        string='HAV.sh Instances',
        domain=[('res_model', '=', 'sale.order')],
    )
    havsh_odoo_count = fields.Integer(
        string='HAV.sh Instance Count',
        compute='_compute_havsh_odoo_count',
    )
    havsh_provisioning_job_ids = fields.One2many(
        'havsh.provisioning.job',
        'res_id',
        string='Provisioning Jobs',
        domain=[('res_model', '=', 'sale.order')],
    )
    havsh_provisioning_job_count = fields.Integer(
        string='Provisioning Job Count',
        compute='_compute_havsh_provisioning_job_count',
    )

    @api.depends('havsh_odoo_ids')
    def _compute_havsh_odoo_count(self):
        for order in self:
            order.havsh_odoo_count = len(order.havsh_odoo_ids)

    @api.depends('havsh_provisioning_job_ids')
    def _compute_havsh_provisioning_job_count(self):
        for order in self:
            order.havsh_provisioning_job_count = len(order.havsh_provisioning_job_ids)

    def _confirm_subscription(self):
        res = super()._confirm_subscription()
        for order in self:
            templates_seen = set()
            for line in order.order_line:
                template = line.product_id.product_tmpl_id.havsh_provisioning_template_id
                if template and template.id not in templates_seen:
                    templates_seen.add(template.id)
                    job = self.env['havsh.provisioning.job'].sudo().create({
                        'name': order.partner_id.name or order.name,
                        'provisioning_template_id': template.id,
                        'res_model': 'sale.order',
                        'res_id': order.id,
                    })
                    job.with_delay()._execute_provisioning()
        return res

    def set_close(self):
        res = super().set_close()
        for order in self:
            if order.subscription_state == '6_churn':
                for odoo_rec in order.havsh_odoo_ids:
                    odoo_rec.with_delay()._havsh_stop()
        return res

    def set_open(self):
        # Capture churned orders before super changes subscription_state
        churned_orders = self.filtered(lambda o: o.subscription_state == '6_churn')
        res = super().set_open()
        for order in churned_orders:
            for odoo_rec in order.havsh_odoo_ids:
                odoo_rec.with_delay()._havsh_start()
        return res

    def action_show_havsh_odoo_instances(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id("hav_sh_base.action_havsh_odoos")
        action['domain'] = [('res_id', '=', self.id), ('res_model', '=', 'sale.order')]
        return action

    def action_show_havsh_provisioning_jobs(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id("hav_sh_base.action_havsh_provisioning_jobs")
        action['domain'] = [('res_id', '=', self.id), ('res_model', '=', 'sale.order')]
        return action
