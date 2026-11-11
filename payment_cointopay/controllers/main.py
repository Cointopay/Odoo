# -*- coding: utf-8 -*-

import logging
import pprint

from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class CoinToPayController(http.Controller):
    _return_url = '/payment/cointopay/return'

    @http.route('/payment/cointopay/return', type='http', auth='public', csrf=False, methods=['GET', 'POST'])
    def cointopay_return(self, **post):
        _logger.info('Coin To Pay form_feedback with post data %s', pprint.pformat(post))  # debug
        tx = request.env['payment.transaction'].sudo()._get_tx_from_notification_data(
            provider_code='cointopay', notification_data=post
        )
        if tx:
            tx._process_notification_data(post)
        return request.redirect('/payment/status')
