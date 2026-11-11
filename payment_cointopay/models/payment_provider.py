import logging
import requests

from werkzeug.urls import url_join, url_encode

from odoo import fields, models, api, _
from odoo.exceptions import ValidationError
from odoo.addons.payment_cointopay import const

_logger = logging.getLogger(__name__)


class PaymentProvider(models.Model):
    _inherit = 'payment.provider'

    code = fields.Selection(
        selection_add=[
            ('cointopay', "Cointopay")
        ],
        ondelete={'cointopay': 'set default'}
    )

    ctp_merchant_id = fields.Char('MerchantId')
    ctp_security_code = fields.Char('SecurityCode')
    ctp_account_api_key = fields.Char('Account API Key')
    ctp_coin_name = fields.Char('Coin Name')
    ctp_coin_id = fields.Char('CoinId', compute='_compute_ctp_coin_id', store=True)

    def _compute_feature_support_fields(self):
        """ Override of `payment` to enable additional features. """
        super()._compute_feature_support_fields()
        self.filtered(lambda p: p.code == 'cointopay').update({
            'support_express_checkout': False,
            'support_manual_capture': 'full_only',
            'support_refund': 'full_only',
            'support_tokenization': False,
        })

    def _get_supported_currencies(self):
        """ Override of `payment` to return the supported currencies. """
        supported_currencies = super()._get_supported_currencies()
        if self.code == 'cointopay':
            supported_currencies = supported_currencies.filtered(
                lambda c: c.name in const.SUPPORTED_CURRENCIES
            )
        return supported_currencies

    def _get_default_payment_method_codes(self):
        """ Override of `payment` to return the default payment method codes. """
        default_codes = super()._get_default_payment_method_codes()
        if self.code != 'cointopay':
            return default_codes
        return const.DEFAULT_PAYMENT_METHOD_CODES

    def _get_cointopay_api_url(self, endpoint=None):
        """Build the CoinToPay URL, ensuring no leading slash in endpoint."""
        base_url = 'https://app.cointopay.com'
        if endpoint:
            endpoint = endpoint.lstrip('/')
            base_url = f'{base_url}/{endpoint}'
        return base_url

    def _allow_cointopay_get_coin(self):
        return (
                self.ctp_merchant_id and
                self.ctp_coin_name and
                self.ctp_account_api_key and
                self.code == 'cointopay' and
                self.state != 'disabled'
        )

    @api.depends('ctp_merchant_id', 'ctp_coin_name', 'ctp_account_api_key', 'state')
    def _compute_ctp_coin_id(self):
        for provider in self:
            if not provider._allow_cointopay_get_coin():
                provider.ctp_coin_id = ''
                continue

            params = provider._get_default_request_values(call='COIN-LIST')

            data = provider._send_cointopay_request(endpoint='/v2REAPI', params=params)
            alt_coins = sorted(data, key=lambda c: (c.get("Name") or "").lower())

            coin = next(
                (c for c in alt_coins if provider.ctp_coin_name.lower() == (c.get("Name") or "").lower()),
                None
            )
            if coin:
                provider.ctp_coin_id = coin.get("ID")
            else:
                provider.ctp_coin_id = ''

    def _get_default_request_values(self, call=False):
        values = {
            'MerchantID': self.ctp_merchant_id,
            'APIKey': self.ctp_account_api_key,
            'output': 'json'
        }
        if call:
            values['Call'] = call

        return values

    def _get_cointopay_headers(self, **kwargs):
        headers = {
            'Accept': 'application/json',
        }
        if 'content_type' in kwargs:
            headers['Content-Type'] = kwargs['content_type']

        return headers

    def _get_cointopay_error_from_response(self, response):
        """Extract error message from CoinToPay HTTP response.

        :param response: requests.Response object returned by the API call
        :return: Raw error message as string extracted from response body
        """
        return response.text

    def _send_cointopay_request(self, endpoint=False, method='GET', params=None, data=None, json_payload=None,
                                **kwargs):
        """Send HTTP request supporting query params and body payload.

        :param endpoint: API endpoint
        :param method: HTTP method (GET, POST, PUT, DELETE, etc.)
        :param params: dict for query string parameters
        :param data: dict or str for form-encoded body
        :param json_payload: dict for JSON body
        :return: requests.Response
        """
        url = self._get_cointopay_api_url(endpoint=endpoint)

        headers = self._get_cointopay_headers(**kwargs)

        response = requests.request(
            method=method,
            url=url,
            params=params,  # Query params (?key=value)
            data=data,  # Body (form-data or raw)
            json=json_payload,  # Body JSON (preferred)
            headers=headers,
            timeout=30
        )

        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            _logger.warning("Cointopay HTTP error: %s", e)
            message = self._get_cointopay_error_from_response(response)
            raise ValidationError(message)
        except Exception as e:
            raise ValidationError(_("An error occurred while communicating with the payment provider: %s") % str(e))

        return response.json()
