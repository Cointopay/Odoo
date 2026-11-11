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
        tx_sudo = request.env['payment.transaction'].sudo()._search_by_reference(
            'cointopay', post
        )
        tx_sudo._process(
            'cointopay', post
        )
        return request.redirect('/payment/status')
