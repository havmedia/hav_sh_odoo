from unittest.mock import patch, MagicMock

from odoo.tests.common import tagged

from .common import HavShSubscriptionTestCommon


@tagged('-at_install', 'post_install')
class TestSaleOrderSubscription(HavShSubscriptionTestCommon):

    def _create_subscription_order(self):
        plan = self.env['sale.subscription.plan'].create({
            'name': 'Monthly',
            'billing_period_value': 1,
            'billing_period_unit': 'month',
        })
        order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'plan_id': plan.id,
            'order_line': [(0, 0, {
                'product_id': self.product.product_variant_id.id,
                'product_uom_qty': 1,
                'price_unit': 100.0,
            })],
        })
        return order

    @patch('odoo.addons.hav_sh_base.models.res_company.requests.request')
    def test_confirm_subscription_creates_provisioning_job(self, mock_request):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'data': {
                'id': 42,
                'uuid': 'prov-uuid-123',
                'status': 'pending',
            }
        }
        mock_response.raise_for_status = MagicMock()
        mock_request.return_value = mock_response

        order = self._create_subscription_order()

        with patch.object(type(self.env['havsh.provisioning.job']), '_execute_provisioning'):
            order.action_confirm()

        jobs = self.env['havsh.provisioning.job'].search([
            ('res_model', '=', 'sale.order'),
            ('res_id', '=', order.id),
        ])
        self.assertEqual(len(jobs), 1)
        self.assertEqual(jobs.provisioning_template_id, self.provisioning_template)
        self.assertEqual(jobs.name, self.partner.name)

    def test_confirm_subscription_no_template_no_job(self):
        """Orders without provisioning template should not create jobs."""
        product_no_tpl = self.env['product.template'].create({
            'name': 'Regular Hosting',
            'type': 'service',
            'recurring_invoice': True,
        })
        plan = self.env['sale.subscription.plan'].create({
            'name': 'Monthly',
            'billing_period_value': 1,
            'billing_period_unit': 'month',
        })
        order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'plan_id': plan.id,
            'order_line': [(0, 0, {
                'product_id': product_no_tpl.product_variant_id.id,
                'product_uom_qty': 1,
                'price_unit': 50.0,
            })],
        })
        order.action_confirm()

        jobs = self.env['havsh.provisioning.job'].search([
            ('res_model', '=', 'sale.order'),
            ('res_id', '=', order.id),
        ])
        self.assertEqual(len(jobs), 0)

    def test_set_close_stops_instances(self):
        """Churning a subscription should stop linked HAV.sh instances."""
        order = self._create_subscription_order()
        order.subscription_state = '3_progress'

        server = self.env['havsh.server'].create({
            'name': 'Test Server',
            'external_id': '1',
            'is_ready_for_odoo': True,
        })
        odoo_instance = self.env['havsh.odoo'].create({
            'name': 'Test Instance',
            'external_id': '99',
            'version': '18.0',
            'type': 'live',
            'state': 'running',
            'server_id': server.id,
            'res_model': 'sale.order',
            'res_id': order.id,
        })

        with patch.object(type(self.env['havsh.odoo']), '_havsh_stop') as mock_stop:
            order.set_close()
            mock_stop.assert_called_once()

    def test_set_open_starts_instances(self):
        """Reopening a churned subscription should start linked HAV.sh instances."""
        order = self._create_subscription_order()
        order.subscription_state = '6_churn'

        server = self.env['havsh.server'].create({
            'name': 'Test Server',
            'external_id': '2',
            'is_ready_for_odoo': True,
        })
        odoo_instance = self.env['havsh.odoo'].create({
            'name': 'Test Instance',
            'external_id': '100',
            'version': '18.0',
            'type': 'live',
            'state': 'running',
            'server_id': server.id,
            'res_model': 'sale.order',
            'res_id': order.id,
        })

        with patch.object(type(self.env['havsh.odoo']), '_havsh_start') as mock_start:
            order.set_open()
            mock_start.assert_called_once()

    def test_pause_does_not_stop(self):
        """Pausing a subscription should NOT stop linked HAV.sh instances."""
        order = self._create_subscription_order()
        order.subscription_state = '3_progress'

        server = self.env['havsh.server'].create({
            'name': 'Test Server',
            'external_id': '3',
            'is_ready_for_odoo': True,
        })
        odoo_instance = self.env['havsh.odoo'].create({
            'name': 'Test Instance',
            'external_id': '101',
            'version': '18.0',
            'type': 'live',
            'state': 'running',
            'server_id': server.id,
            'res_model': 'sale.order',
            'res_id': order.id,
        })

        with patch.object(type(self.env['havsh.odoo']), '_havsh_stop') as mock_stop:
            order.write({'subscription_state': '4_paused'})
            mock_stop.assert_not_called()
