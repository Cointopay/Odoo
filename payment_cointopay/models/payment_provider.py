# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models

from odoo.addons.payment_cointopay import const


class PaymentProvider(models.Model):
    _inherit = "payment.provider"

    code = fields.Selection(
        selection_add=[("cointopay", "Cointopay")],
        ondelete={"cointopay": "set default"},
    )
    ctp_merchant_id = fields.Char(
        string="Merchant ID",
        help="The merchant ID of your Cointopay account.",
        required_if_provider="cointopay",
        groups="base.group_user",
    )
    ctp_security_code = fields.Char(
        string="Security Code",
        help="The security code of your Cointopay account.",
        required_if_provider="cointopay",
        groups="base.group_system",
    )
    ctp_coin_id = fields.Char(
        string="Coin ID",
        help="The technical ID of the crypto coin used to receive the payments.",
        required_if_provider="cointopay",
        groups="base.group_user",
    )

    def _get_default_payment_method_codes(self):
        """Override of `payment` to activate the Cointopay payment method on install."""
        res = super()._get_default_payment_method_codes() if hasattr(
            super(), "_get_default_payment_method_codes"
        ) else set()
        if self.code == "cointopay":
            return set(const.DEFAULT_PAYMENT_METHOD_CODES)
        return res

    def _get_removal_values(self):
        """Override of `payment` to reset the Cointopay credentials on uninstall."""
        values = super()._get_removal_values()
        values.update({
            "ctp_merchant_id": False,
            "ctp_security_code": False,
            "ctp_coin_id": False,
        })
        return values
