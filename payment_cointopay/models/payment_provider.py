import logging

from werkzeug.urls import url_join, url_encode

from odoo import fields, models, api, _
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

    # === REQUEST HELPERS === #

    def _build_request_url(self, endpoint, **kwargs):
        """Override of `payment` to build the request URL."""
        if self.code != 'cointopay':
            return super()._build_request_url(endpoint, **kwargs)
        endpoint = endpoint.lstrip('/')
        return url_join('https://app.cointopay.com/', endpoint)

    def _parse_response_error(self, response):
        """Override of `payment` to parse the error message.
        :param requests.Response or requests.Response.json() response: The response to parse.
        """
        if self.code != 'cointopay':
            return super()._parse_response_error(response)

        try:
            data = response.json()
            if 'message' in data:
                return data['message']

            return _("An error occurred while communicating with the payment provider")

        except Exception as e:
            _logger.warning("Cointopay HTTP error: %s", e)
            return response.text

    def _parse_response_content(self, response, **kwargs):
        """Override of `payment` to parse the response content."""
        if self.code != 'cointopay':
            return super()._parse_response_content(response, **kwargs)
        return response.json()

    def _build_request_headers(self, *args, **kwargs):
        """Override of `payment` to build the request headers."""
        if self.code != 'cointopay':
            return super()._build_request_headers(*args, **kwargs)

        headers = {
            'Accept': 'application/json',
        }
        if 'content_type' in kwargs:
            headers['Content-Type'] = kwargs['content_type']

        return headers

    def _allow_cointopay_get_coin(self):
        return (
            self.ctp_merchant_id and
            self.ctp_coin_name and
            self.ctp_account_api_key and
            self.code == 'cointopay' and
            self.state != 'disabled'
        )

    @api.depends('ctp_merchant_id', 'ctp_coin_name', 'ctp_account_api_key')
    def _compute_ctp_coin_id(self):
        for provider in self:
            if not provider._allow_cointopay_get_coin():
                provider.ctp_coin_id = ''
                continue

            params = provider._get_default_request_values(call='COIN-LIST')

            data = provider._send_api_request(
                method='GET',
                params=params,
                endpoint='v2REAPI'
            )

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
