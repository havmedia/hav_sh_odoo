import hashlib
import hmac
import json
from unittest.mock import MagicMock, patch

from odoo.tests import tagged

from .common import HavShBaseCase


@tagged('post_install', '-at_install')
class TestResCompany(HavShBaseCase):

    # ------------------------------------------------------------------
    # Signature validation
    # ------------------------------------------------------------------
    def _compute_signature(self, payload, token='test-webhook-token'):
        payload_str = json.dumps(payload, separators=(',', ':')).replace('/', '\\/')
        return hmac.new(
            token.encode('utf-8'),
            payload_str.encode('utf-8'),
            hashlib.sha256,
        ).hexdigest()

    def test_validate_signature_correct(self):
        payload = [{'module': 'ServiceOdoo', 'event': 'created', 'data': {}}]
        signature = self._compute_signature(payload)
        self.assertTrue(self.env.company._validate_signature(payload, signature))

    def test_validate_signature_incorrect(self):
        payload = [{'module': 'ServiceOdoo', 'event': 'created', 'data': {}}]
        self.assertFalse(self.env.company._validate_signature(payload, 'bad-signature'))

    def test_validate_signature_empty(self):
        payload = [{'module': 'ServiceOdoo', 'event': 'created', 'data': {}}]
        self.assertFalse(self.env.company._validate_signature(payload, ''))
        self.assertFalse(self.env.company._validate_signature(payload, False))

    # ------------------------------------------------------------------
    # API call
    # ------------------------------------------------------------------
    @patch('hav_sh_base.models.res_company.requests')
    def test_call_hav_sh_get(self, mock_requests):
        mock_response = MagicMock()
        mock_response.json.return_value = {'data': 'test'}
        mock_response.raise_for_status.return_value = None
        mock_requests.request.return_value = mock_response

        result = self.env.company.call_hav_sh('service-odoo/1', method='GET')

        self.assertEqual(result, {'data': 'test'})
        mock_requests.request.assert_called_once_with(
            method='GET',
            url='https://test.hav.sh/api/service-odoo/1',
            headers={
                'Authorization': 'Bearer test-api-token',
                'Content-Type': 'application/json',
                'Accept': 'application/json',
            },
            json=None,
            verify=True,
        )

    @patch('hav_sh_base.models.res_company.requests')
    def test_call_hav_sh_post(self, mock_requests):
        mock_response = MagicMock()
        mock_response.json.return_value = {'data': {'id': 1}}
        mock_response.raise_for_status.return_value = None
        mock_requests.request.return_value = mock_response

        payload = {'name': 'test'}
        result = self.env.company.call_hav_sh('service-odoo', payload=payload, method='POST')

        self.assertEqual(result, {'data': {'id': 1}})
        call_args = mock_requests.request.call_args
        self.assertEqual(call_args.kwargs['method'], 'POST')
        self.assertEqual(call_args.kwargs['json'], {'name': 'test'})

    @patch('hav_sh_base.models.res_company.requests')
    def test_call_hav_sh_http_error(self, mock_requests):
        import requests as real_requests
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = real_requests.exceptions.HTTPError('404')
        mock_requests.request.return_value = mock_response
        mock_requests.exceptions = real_requests.exceptions

        with self.assertRaises(real_requests.exceptions.HTTPError):
            self.env.company.call_hav_sh('service-odoo/999', method='GET')

    @patch('hav_sh_base.models.res_company.requests')
    def test_call_hav_sh_non_json_response(self, mock_requests):
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.side_effect = ValueError('No JSON')
        mock_response.text = 'OK'
        mock_requests.request.return_value = mock_response

        result = self.env.company.call_hav_sh('service-odoo/1', method='GET')
        self.assertEqual(result, 'OK')

    @patch('hav_sh_base.models.res_company.requests')
    def test_call_hav_sh_disable_cert_check(self, mock_requests):
        self.env.company.hav_sh_disable_cert_check = True
        mock_response = MagicMock()
        mock_response.json.return_value = {}
        mock_response.raise_for_status.return_value = None
        mock_requests.request.return_value = mock_response

        self.env.company.call_hav_sh('service-odoo', method='GET')
        call_args = mock_requests.request.call_args
        self.assertFalse(call_args.kwargs['verify'])

    def test_call_hav_sh_url_construction(self):
        """Trailing slash on host and leading slash on endpoint are handled."""
        self.env.company.hav_sh_api_host = 'https://test.hav.sh/'
        with patch('hav_sh_base.models.res_company.requests') as mock_requests:
            mock_response = MagicMock()
            mock_response.json.return_value = {}
            mock_response.raise_for_status.return_value = None
            mock_requests.request.return_value = mock_response

            self.env.company.call_hav_sh('/service-odoo', method='GET')
            call_args = mock_requests.request.call_args
            self.assertEqual(call_args.kwargs['url'], 'https://test.hav.sh/api/service-odoo')
