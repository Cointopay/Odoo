# -*- coding: utf-8 -*-

import logging
import pprint
import werkzeug

from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class CoinToPayController(http.Controller):
    return_url = '/payment/cointopay/return'
    cancel_url = '/payment/cointopay/cancel'

    @http.route([
        '/payment/cointopay/return',
        '/payment/cointopay/cancel',
    ], type='http', auth='none', csrf=False, methods=['GET', 'POST'])
    def cointopay_return(self, **post):
        _logger.info('Coin To Pay form_feedback with post data %s', pprint.pformat(post))  # debug
        request.env['payment.transaction'].sudo().form_feedback(post, 'cointopay')
	return_url = post.get('addreturnurl', '/shop/confirmation')
        return werkzeug.utils.redirect(return_url)
