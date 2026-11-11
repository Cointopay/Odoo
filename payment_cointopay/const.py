# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

# Checkout endpoint. Cointopay exposes the same endpoint for live and test payments; the
# environment is selected by the credentials configured on the provider.
PAYMENT_URL = "https://app.cointopay.com/MerchantAPI?Checkout=true"

# Routes called by Cointopay when the customer comes back from the checkout.
RETURN_ROUTE = "/payment/cointopay/return"
CANCEL_ROUTE = "/payment/cointopay/cancel"
STATUS_ROUTE = "/payment/status"

# Technical code of the payment method created for the provider.
PAYMENT_METHOD_CODE = "crypto"
DEFAULT_PAYMENT_METHOD_CODES = {PAYMENT_METHOD_CODE}

# Mapping of the Cointopay statuses to the Odoo transaction states.
PAYMENT_STATUS_MAPPING = {
    "done": ("paid", "success", "successful", "completed", "confirmed"),
    "pending": ("pending", "processing", "waiting", "notenough"),
    "canceled": ("failed", "failure", "cancel", "canceled", "cancelled", "expired", "error"),
}
