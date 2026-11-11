# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import pprint

from odoo import http
from odoo.exceptions import ValidationError
from odoo.http import request

from odoo.addons.payment_cointopay import const

import logging

_logger = logging.getLogger(__name__)


class CointopayController(http.Controller):

    @http.route(
        const.RETURN_ROUTE,
        type="http",
        auth="public",
        methods=["GET", "POST"],
        csrf=False,
        save_session=False,
    )
    def cointopay_return_from_checkout(self, **data):
        """Process the payment data sent by Cointopay after the checkout.

        :param dict data: The payment data sent by Cointopay.
        :return: A redirection to the payment status page.
        :rtype: odoo.http.Response
        """
        _logger.info(
            "Handling redirection from Cointopay with data:\n%s", pprint.pformat(data)
        )
        self._process_payment_data(data)
        return request.redirect(const.STATUS_ROUTE)

    @http.route(
        const.CANCEL_ROUTE,
        type="http",
        auth="public",
        methods=["GET", "POST"],
        csrf=False,
        save_session=False,
    )
    def cointopay_cancel_from_checkout(self, **data):
        """Process the cancellation data sent by Cointopay after the checkout.

        :param dict data: The payment data sent by Cointopay.
        :return: A redirection to the payment status page.
        :rtype: odoo.http.Response
        """
        _logger.info(
            "Handling cancellation from Cointopay with data:\n%s", pprint.pformat(data)
        )
        data = dict(data)
        data.setdefault("status", "failed")
        self._process_payment_data(data)
        return request.redirect(const.STATUS_ROUTE)

    @staticmethod
    def _process_payment_data(data):
        """Hand the payment data over to the transaction model.

        :param dict data: The payment data sent by Cointopay.
        :return: None
        """
        tx_model = request.env["payment.transaction"].sudo()
        if hasattr(tx_model, "_search_by_reference"):
            # Odoo 19+: search the transaction by reference first.
            tx_sudo = tx_model._search_by_reference("cointopay", data)
            if tx_sudo:
                if hasattr(tx_sudo, "_record"):
                    # Odoo 20+: record the payment data and let the cron process it.
                    tx_sudo._record(data)
                else:
                    # Odoo 19: process the payment data synchronously.
                    tx_sudo._process("cointopay", data)
        else:
            # Odoo 16-18: the payment data are processed synchronously.
            try:
                tx_model._handle_notification_data("cointopay", data)
            except ValidationError as error:
                _logger.warning("Could not process the Cointopay data: %s", error)
