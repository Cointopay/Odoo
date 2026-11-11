# -*- coding: utf-8 -*-
# Part of Wclik Corporation. See LICENSE file for full copyright and licensing details.

import logging
from odoo import api, SUPERUSER_ID, Command

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {'active_test': False})
    bank_account = env.ref(
        'payment.payment_method_bank_account',
        raise_if_not_found=False
    )
    if bank_account:
        _logger.info('[MIGRATION] Bank account payment method found. Linking it to CoinToPay provider.')

        cointopay_method = env.ref(
            'payment_cointopay.payment_method_cointopay',
            raise_if_not_found=False
        )

        method_ids = [m.id for m in [cointopay_method, bank_account] if m]
        providers = env['payment.provider'].search([
            ('code', '=', 'cointopay')
        ])

        providers.write({
            'payment_method_ids': [Command.set(method_ids)]
        })
