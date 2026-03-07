from odoo.http import request

from odoo import http


class HavShWebhookController(http.Controller):

    @http.route('/hav_sh/incoming_webhook', auth='public', csrf=False)
    def incoming_hav_sh_webhook(self):
        supplied_signature = request.httprequest.headers.get("signature", False)
        payload = request.httprequest.json

        if not request.env.company._validate_signature(payload, supplied_signature):
            return request.make_json_response(data={
                'message': 'Invalid Signature',
                'status': 403},
                status=403
            )

        havsh_odoo_model = request.env['havsh.odoo']
        havsh_server_model = request.env['havsh.server']

        for event in payload:
            if event['module'] == 'ServiceOdoo':
                if event['event'] == 'created':
                    havsh_odoo_model.sudo().create_from_webhook(event['data'])
                if event['event'] == 'updated':
                    havsh_odoo_model.sudo().update_from_webhook(event['data'])
                if event['event'] == 'deleted':
                    havsh_odoo_model.sudo().delete_from_webhook(event['data'])

            if event['module'] == 'Server':
                if event['event'] == 'created':
                    havsh_server_model.sudo().create_from_webhook(event['data'])
                if event['event'] == 'updated':
                    havsh_server_model.sudo().update_from_webhook(event['data'])
                if event['event'] == 'deleted':
                    havsh_server_model.sudo().delete_from_webhook(event['data'])

        return request.make_json_response(data={
            'message': 'OK',
            'status': 200,
        });
