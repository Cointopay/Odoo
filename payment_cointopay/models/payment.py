import logging
import json
from hashlib import sha1
import urlparse
import urllib, urllib2
from odoo import api, fields, models, _
from odoo.addons.payment.models.payment_acquirer import ValidationError
from odoo.addons.payment_cointopay.controllers.main import CoinToPayController
from odoo.tools.float_utils import float_compare

_logger = logging.getLogger(__name__)


def get_cointopay_urls(environment):
    if environment == 'prod':
        return 'https://app.cointopay.com/MerchantAPI?Checkout=true'
    else:
        return 'https://app.cointopay.com/MerchantAPI?Checkout=true'


class AcquirerCoinToPay(models.Model):
    _inherit = 'payment.acquirer'

    provider = fields.Selection(selection_add=[('cointopay', 'Cointopay')])
    ctp_merchant_id = fields.Char('MerchantId', required_if_provider='cointopay', groups='base.group_user')
    ctp_security_code = fields.Char('SecurityCode', required_if_provider='cointopay', groups='base.group_user')
    ctp_coin_id = fields.Char('CoinId', required_if_provider='cointopay', groups='base.group_user')
   

    @api.multi
    def cointopay_form_generate_values(self, values):
        self.ensure_one()
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        cointopay_tx_values = dict(values)
        cointopay_tx_values.update({
            'MerchantID': self.ctp_merchant_id,
            'SecurityCode': self.ctp_security_code,
            'AltCoinID': self.ctp_coin_id,
            'Amount': values['amount'],
            'inputCurrency': values['currency'] and values['currency'].name or '',
            'CustomerReferenceNr': values['reference'],
            'transactionconfirmurl': '%s' % urlparse.urljoin(base_url, CoinToPayController.return_url + '?Amount=%s' %(values['amount'])),
            'transactionfailurl': '%s' % urlparse.urljoin(base_url, CoinToPayController.cancel_url + '?Amount=%s' %(values['amount'])),
            'addreturnurl': cointopay_tx_values.pop('return_url', ''),
        })
        return cointopay_tx_values

    @api.multi
    def cointopay_get_form_action_url(self):
        self.ensure_one()
        return get_cointopay_urls(self.environment)


class PaymentTransactionCointopay(models.Model):
    _inherit = 'payment.transaction'

    # Create fields in database
    ctp_transaction_id = fields.Char('Transaction ID', required_if_provider='cointopay', groups='base.group_user')
    ctp_confirm_code = fields.Char('Confirm Code', required_if_provider='cointopay', groups='base.group_user')

    @api.model
    def _cointopay_form_get_tx_from_data(self, data):
        """ Given a data dict coming from cointopay, verify it and find the related
        transaction record. """
        origin_data = dict(data)
        reference = data.get('CustomerReferenceNr')
        transaction_id = data.get('TransactionID')
        
        transaction = self.search([('reference', '=', reference)])

        if not transaction:
            error_msg = (_('Cointopay: received data for reference %s; no order found') % reference)
            raise ValidationError(error_msg)
        elif len(transaction) > 1:
            error_msg = (_('Cointopay: received data for reference %s; multiple orders found') % reference)
            raise ValidationError(error_msg)

        return transaction

    @api.multi
    def _cointopay_form_get_invalid_parameters(self, data):
        invalid_parameters = []

        if self.acquirer_reference and data.get('CustomerReferenceNr') != self.acquirer_reference:
            invalid_parameters.append(
                ('Transaction Id', data.get('CustomerReferenceNr'), self.acquirer_reference))
        # check what is bought
        if float_compare(float(data.get('Amount', '0.0')), self.amount, 2) != 0:
            invalid_parameters.append(('Amount', data.get('Amount'), '%.2f' % self.amount))

        return invalid_parameters

    @api.multi
    def _cointopay_form_validate(self, data):
        status = data.get('status')
        merchant_id = data.get('MerchantID')
        reference = data.get('CustomerReferenceNr')
        transaction_id = data.get('TransactionID')
        validate_date = fields.Datetime.now()
        confirm_code = data.get('ConfirmCode')
        # Verify the payment status
        url = "https://merchant.ebitcoin.org/v2REAPI?MerchantID=" + merchant_id + "&Call=QA&APIKey=_&output=json&TransactionID=" + transaction_id + "&ConfirmCode=" + confirm_code
	
	try:
		contents = json.loads(urllib2.urlopen(url).read())
	except urllib2.HTTPError, e:
    		_logger.info(e.fp.read())

	if contents.get('Status', '') != status:
            status = 'failed'

        # Save order in database
        if status == 'paid':
            not_enough = data.get('notenough', 0)
            if not_enough == 1:
                res = {
                    'state': 'pending',
            	    'acquirer_reference': reference,
                    'ctp_transaction_id': transaction_id,
                    'ctp_confirm_code': confirm_code,
                    'date_validate': validate_date
                }
                return self.write(res)
            else:
                res = {
                    'state': 'done',
                    'acquirer_reference': reference,
                    'ctp_transaction_id': transaction_id,
                    'ctp_confirm_code': confirm_code,
                    'date_validate': validate_date
                }
                return self.write(res)

        elif status == 'failed':
            res = {
                'state': 'cancel',
                'acquirer_reference': reference,
                'ctp_transaction_id': transaction_id,
                'ctp_confirm_code': confirm_code,
                'date_validate': validate_date
            }
            return self.write(res)
