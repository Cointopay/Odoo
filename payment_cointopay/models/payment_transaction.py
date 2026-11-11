import logging
import pprint
import html
import requests

from werkzeug.urls import url_join, url_encode
from odoo import fields, models, _
from odoo.addons.payment import utils as payment_utils

from odoo.addons.payment_cointopay.controllers.main import CoinToPayController
from odoo.addons.payment_cointopay import const
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class PaymentTransaction(models.Model):
    _inherit = 'payment.transaction'

    ctp_confirm_code = fields.Char('Cointopay Confirm Code')

    def _get_specific_rendering_values(self, processing_values):
        res = super()._get_specific_rendering_values(processing_values)
        if self.provider_code != 'cointopay':
            return res

        params_values = self._get_cointopay_values()
        data = self.provider_id._send_cointopay_request(
            endpoint='MerchantAPI', params=params_values
        )

        if self.payment_method_code == 'cointopay':
            if not 'shortURL' in data:
                raise ValidationError(_('Error getting payment URL'))

            self.provider_reference = data['TransactionID']

            return {
                'api_url': data['shortURL'],
            }

        if self.payment_method_code == 'bank_account':
            if not 'Security' in data:
                raise ValidationError(_('Error getting payment URL'))

            return {
                'api_url': f"https://artemis.cointopay.com/transak/pay?confirmCode={data['Security']}",
            }

        raise ValidationError(_('Error, payment method no supported by provider'))

    def _get_tx_from_notification_data(self, provider_code, notification_data):
        """ Override of payment to find the transaction based on Cointopay data.

        :param str provider_code: The code of the provider that handled the transaction
        :param dict notification_data: The notification data sent by the provider
        :return: The transaction if found
        :rtype: recordset of `payment.transaction`
        :raise: ValidationError if inconsistent data were received
        :raise: ValidationError if the data match no transaction
        """
        tx = super()._get_tx_from_notification_data(provider_code, notification_data)
        if provider_code != 'cointopay':
            return tx

        reference = notification_data.get('reference')
        tx = self.search([
            ('reference', '=', reference), ('provider_code', '=', 'cointopay')
        ])

        return tx

    def _process_notification_data(self, notification_data):
        """Override to process the transaction based on CoinToPay data."""
        super()._process_notification_data(notification_data)
        if self.provider_code != 'cointopay':
            return

        # --- Access token verification ---
        token_values = [self.reference, self.amount, self.currency_id.name]
        access_token = notification_data.get('access_token')

        if not access_token or not payment_utils.check_access_token(access_token, token_values):
            _logger.warning('Cointopay access token is invalid.')
            return

        # --- Verify the payment status from CoinToPay ---
        transaction_id = notification_data.get('TransactionID')
        url_params = {
            **self.provider_id._get_default_request_values(call='Transactiondetail'),
            'TransactionID': transaction_id,
        }

        try:
            data = self.provider_id._send_cointopay_request(endpoint='/v2REAPI', params=url_params)
            _logger.info('CoinToPay response data: %s', pprint.pformat(data))

            status_code = data.get('status_code')
            message = data.get('message') or False
            if status_code != 200:
                _logger.warning(
                    'CoinToPay request failed with status code %d, message: %s, reference: %s',
                    status_code,
                    message,
                    self.reference
                )
                return

            server_data = data.get('data')

            # --- Reference validation ---
            server_ref = server_data.get('CustomerReferenceNr')
            decoded_ref = html.unescape(server_ref) if server_ref else None

            if decoded_ref != self.reference:
                _logger.warning(
                    "CoinToPay reference mismatch. Expected %s but got %s (decoded %s)",
                    self.reference, server_ref, decoded_ref
                )
                return

            self.provider_reference = transaction_id,
            self.ctp_confirm_code = server_data.get('Security')

            # from notification_data
            status = notification_data.get('status')

            # --- Status mapping ---
            if server_data.get("Status") != status:
                status = 'failed'

            if status in const.PAYMENT_STATUS_MAPPING['done']:
                not_enough = server_data.get('NotEnough', 0)
                if not_enough == 1:
                    self._set_pending(state_message=message)
                else:
                    self._set_done(state_message=message)

            elif status in const.PAYMENT_STATUS_MAPPING['failed']:
                self._set_error(state_message=message)

        except Exception as e:
            _logger.error("Error processing CoinToPay notification: %s", str(e))
            return

    def _get_cointopay_values(self):

        token_values = [self.reference, self.amount, self.currency_id.name]
        url_values = url_encode({
            'reference': self.reference,
            'amount': self.amount,
            'currency': self.currency_id.name,
            'access_token': payment_utils.generate_access_token(token_values)
        })
        base_url = self.provider_id.get_base_url()
        return_url = url_join(
            base_url,
            f'{CoinToPayController._return_url}?{url_values}'
        )

        return {
            'SecurityCode': self.provider_id.ctp_security_code,
            'AltCoinID': self.provider_id.ctp_coin_id,
            'Amount': self.amount,
            'inputCurrency': self.currency_id.name,
            'CustomerReferenceNr': self.reference,
            'transactionconfirmurl': return_url,
            'transactionfailurl': return_url,
            'addreturnurl': return_url,
            'Checkout': 'true',
            **self.provider_id._get_default_request_values()
        }
