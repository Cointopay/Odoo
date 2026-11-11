# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging
from urllib.parse import urljoin

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

from odoo.addons.payment_cointopay import const

_logger = logging.getLogger(__name__)

class PaymentTransaction(models.Model):
    _inherit = "payment.transaction"

    ctp_transaction_id = fields.Char(
        string="Cointopay Transaction ID",
        readonly=True,
        groups="base.group_user",
        copy=False,
    )
    ctp_confirm_code = fields.Char(
        string="Cointopay Confirm Code",
        readonly=True,
        groups="base.group_user",
        copy=False,
    )

    def _get_specific_rendering_values(self, processing_values):
        """Override of `payment` to return Cointopay-specific rendering values.

        Note: self.ensure_one() from `_get_processing_values`

        :param dict processing_values: The generic and specific processing values of the
                                       transaction.
        :return: The dict of provider-specific rendering values.
        :rtype: dict
        """
        res = super()._get_specific_rendering_values(processing_values)
        if self.provider_code != "cointopay":
            return res

        base_url = self.provider_id.get_base_url()
        return_url = urljoin(base_url, const.RETURN_ROUTE)
        cancel_url = urljoin(base_url, const.CANCEL_ROUTE)
        status_url = urljoin(base_url, const.STATUS_ROUTE)
        url_params = {
            "MerchantID": self.provider_id.ctp_merchant_id,
            "SecurityCode": self.provider_id.ctp_security_code,
            "AltCoinID": self.provider_id.ctp_coin_id,
            "Amount": self.amount,
            "inputCurrency": self.currency_id.name,
            "CustomerReferenceNr": self.reference,
            "transactionconfirmurl": return_url,
            "transactionfailurl": cancel_url,
            "addreturnurl": status_url,
        }
        return {
            **res,
            "api_url": const.PAYMENT_URL,
            "url_params": url_params,
        }

    @api.model
    def _extract_reference(self, provider_code, payment_data):
        """Override of `payment` to extract the reference from the payment data."""
        if provider_code != "cointopay":
            if hasattr(super(), "_extract_reference"):  # Odoo 19+
                return super()._extract_reference(provider_code, payment_data)
            return payment_data.get("reference")
        return (
            payment_data.get("CustomerReferenceNr")
            or payment_data.get("reference")
        )

    def _extract_amount_data(self, payment_data):
        """Override of `payment` to extract the amount and currency from the payment data."""
        if self.provider_code != "cointopay":
            if hasattr(super(), "_extract_amount_data"):  # Odoo 19+
                return super()._extract_amount_data(payment_data)
            return None

        amount = payment_data.get("Amount") or payment_data.get("amount")
        if amount in (None, ""):
            # No amount in the payment data: skip the amount validation.
            return None
        currency_code = (
            payment_data.get("inputCurrency")
            or payment_data.get("Currency")
            or payment_data.get("currency")
            or self.currency_id.name
        )
        return {"amount": float(amount), "currency_code": currency_code}

    def _apply_updates(self, payment_data):
        """Override of `payment` to update the transaction with the Cointopay data."""
        if self.provider_code != "cointopay":
            if hasattr(super(), "_apply_updates"):  # Odoo 19+
                return super()._apply_updates(payment_data)
            return None

        # Store the provider reference and the Cointopay-specific references.
        self.provider_reference = (
            payment_data.get("TransactionID")
            or payment_data.get("TransactionId")
            or self.provider_reference
        )
        self.ctp_transaction_id = self.provider_reference
        self.ctp_confirm_code = payment_data.get("ConfirmCode") or self.ctp_confirm_code

        status = (
            payment_data.get("Status")
            or payment_data.get("status")
            or ""
        ).lower()
        not_enough = str(payment_data.get("notenough", "0")).lower() in ("1", "true", "yes")

        if not_enough or status in const.PAYMENT_STATUS_MAPPING["pending"]:
            self._set_pending()
        elif status in const.PAYMENT_STATUS_MAPPING["done"]:
            self._set_done()
        elif status in const.PAYMENT_STATUS_MAPPING["canceled"]:
            self._set_canceled()
        else:
            error_msg = _(
                "Cointopay: received data with an unknown status (%(status)s) for transaction "
                "with reference %(reference)s.",
                status=status or _("empty"),
                reference=self.reference,
            )
            _logger.warning(error_msg)
            self._set_error(error_msg)

    # === COMPATIBILITY WITH ODOO 16-18 === #

    @api.model
    def _get_tx_from_notification_data(self, provider_code, notification_data):
        """Override of `payment` to find the transaction based on the Cointopay data.

        This method is only used by Odoo 16-18. Odoo 19+ uses `_search_by_reference`.
        """
        if provider_code != "cointopay":
            if hasattr(super(), "_get_tx_from_notification_data"):  # Odoo 16-18
                return super()._get_tx_from_notification_data(provider_code, notification_data)
            return self

        reference = self._extract_reference(provider_code, notification_data)
        if not reference:
            raise ValidationError(
                _("Cointopay: received data with a missing reference.")
            )
        tx = self.search([
            ("reference", "=", reference),
            ("provider_code", "=", provider_code),
        ])
        if not tx:
            raise ValidationError(
                _(
                    "Cointopay: received data for reference %(reference)s; no order found.",
                    reference=reference,
                )
            )
        return tx

    def _process_notification_data(self, notification_data):
        """Override of `payment` to process the Cointopay data.

        This method is only used by Odoo 16-18. Odoo 19+ uses `_apply_updates`.
        """
        if self.provider_code != "cointopay":
            if hasattr(super(), "_process_notification_data"):  # Odoo 16-18
                return super()._process_notification_data(notification_data)
            return None
        return self._apply_updates(notification_data)
