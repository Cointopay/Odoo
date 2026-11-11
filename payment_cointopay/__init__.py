# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import base64
import logging

from odoo import SUPERUSER_ID, api, tools

from . import controllers, models

try:  # Odoo 20+ wraps binary values in a dedicated type.
    from odoo.tools import BinaryBytes
except ImportError:  # Odoo 17-19 use base64-encoded strings.
    BinaryBytes = None

_logger = logging.getLogger(__name__)

COINTOPAY_METHOD_ICON = "payment_cointopay/static/src/img/cointopay_icon.png"


def _get_env(env_or_cr, registry=None):
    """Return an environment whatever the hook signature of the running Odoo version."""
    if registry is not None:  # Odoo <= 16 calls hooks with (cr, registry)
        return api.Environment(env_or_cr, SUPERUSER_ID, {})
    return env_or_cr  # Odoo >= 17 calls hooks with (env)


def _ensure_payment_method(env, provider):
    """Create and link the Cointopay payment method to the given provider.

    Odoo 17 introduced the `payment.method` model (with a many2many `provider_ids` field) and
    Odoo 20 changed it to a many2one `provider_id` field. The record is therefore created
    programmatically instead of through a data file so that the same module works on both APIs.
    Odoo 16 has no `payment.method` model; nothing is done in that case.
    """
    if "payment.method" not in env:
        return

    PaymentMethod = env["payment.method"]
    uses_provider_id = "provider_id" in PaymentMethod._fields

    if uses_provider_id:
        domain = [("code", "=", "crypto"), ("provider_id", "=", provider.id)]
    else:
        domain = [("code", "=", "crypto"), ("provider_ids", "in", provider.id)]

    payment_method = PaymentMethod.with_context(active_test=False).search(domain, limit=1)
    if not payment_method:
        values = {
            "name": "Crypto",
            "code": "crypto",
            "sequence": 10,
            "active": True,
        }
        try:
            with tools.file_open(COINTOPAY_METHOD_ICON, "rb") as icon:
                icon_bytes = icon.read()
            values["image"] = (
                BinaryBytes(icon_bytes)
                if BinaryBytes is not None
                else base64.b64encode(icon_bytes)
            )
        except FileNotFoundError:
            _logger.warning("Could not find the Cointopay payment method icon.")
        if uses_provider_id:
            values["provider_id"] = provider.id
        else:
            values["provider_ids"] = [(6, 0, [provider.id])]
        payment_method = PaymentMethod.create(values)
    else:
        # Reactivate the payment method if it was archived by a previous uninstallation.
        payment_method.active = True
        if not uses_provider_id:
            payment_method.write({"provider_ids": [(4, provider.id)]})

    # On Odoo 17-19, the provider also has its own many2many field.
    provider_field = provider._fields.get("payment_method_ids")
    if provider_field is not None and provider_field.type == "many2many":
        provider.write({"payment_method_ids": [(4, payment_method.id)]})


def _ensure_module_id(env, providers):
    """Link the providers to this module when the link is missing.

    The link is normally set by `data/payment_provider_data.xml`, but that file is
    `noupdate="1"`, so providers created by an older version of the module keep
    `module_id = False`. Odoo then considers the provider as "not installed" and
    refuses to remove its accounting payment method line during uninstallation.
    """
    module = env.ref("base.module_payment_cointopay", raise_if_not_found=False)
    if module:
        providers.filtered(lambda p: not p.module_id).module_id = module


def post_init_hook(env_or_cr, registry=None):
    """Set up the Cointopay provider after the module installation."""
    env = _get_env(env_or_cr, registry)
    providers = env["payment.provider"].search([("code", "=", "cointopay")])
    _ensure_module_id(env, providers)
    for provider in providers:
        _ensure_payment_method(env, provider)
    if providers:
        providers[0]._setup_provider("cointopay")


def uninstall_hook(env_or_cr, registry=None):
    """Clean up the Cointopay provider data on module uninstallation."""
    env = _get_env(env_or_cr, registry)
    providers = env["payment.provider"].search([("code", "=", "cointopay")])
    if "payment.method" in env and providers:
        PaymentMethod = env["payment.method"]
        if "provider_id" in PaymentMethod._fields:
            domain = [("code", "=", "crypto"), ("provider_id", "in", providers.ids)]
        else:
            domain = [("code", "=", "crypto"), ("provider_ids", "in", providers.ids)]
        PaymentMethod.search(domain).active = False
    if providers:
        providers._remove_provider("cointopay")
