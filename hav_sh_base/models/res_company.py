import hashlib
import hmac
import json

import requests

from odoo import api, fields, models


class Company(models.Model):
    _inherit = 'res.company'

    hav_sh_webhook_token = fields.Char('HAV.sh Webhook Token')
    hav_sh_api_token = fields.Char('HAV.sh API Token')
    hav_sh_api_host = fields.Char('HAV.sh API Host', default='https://hav.sh')
    hav_sh_disable_cert_check = fields.Boolean('HAV.sh Disable Cert Check', default=False, help='Disable cert check for local development')

    def _validate_signature(self, payload, supplied_signature) -> bool:
        self.ensure_one()

        if not supplied_signature:
            return False

        calculated_signature = hmac.new(
            self.hav_sh_webhook_token.encode('utf-8'),
            json.dumps(payload, separators=(',', ':')).replace('/', '\\/').encode('utf-8'),
            hashlib.sha256
        ).hexdigest()

        if calculated_signature != supplied_signature:
            return False

        return True

    def call_hav_sh(self, endpoint, payload=None, method='GET'):
        self.ensure_one()

        url = f"{self.hav_sh_api_host.rstrip('/')}/api/{endpoint.lstrip('/')}"

        headers = {
            "Authorization": f"Bearer {self.hav_sh_api_token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        try:
            response = requests.request(
                method=method.upper(),
                url=url,
                headers=headers,
                json=payload,
                verify=not self.hav_sh_disable_cert_check
            )

            response.raise_for_status()

            try:
                return response.json()
            except ValueError:
                return response.text

        except requests.exceptions.RequestException as e:
            raise
