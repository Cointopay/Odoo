# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import SUPERUSER_ID, api


def migrate(cr, version):
    """Link the existing Cointopay provider to this module.

    Before version 1.1 the provider was created without `module_id`. Odoo then
    reports `module_state = False` and refuses to uninstall the module while the
    provider owns an `account.payment.method.line`:

        You can't delete a payment method that is linked to an installed provider.

    The data file is `noupdate="1"`, so the new `module_id` value added to
    `data/payment_provider_data.xml` is only applied to fresh installs; existing
    providers are repaired here.
    """
    if not version:
        # Fresh installation: the data file already sets `module_id`.
        return

    env = api.Environment(cr, SUPERUSER_ID, {})
    module = env.ref("base.module_payment_cointopay", raise_if_not_found=False)
    if not module:
        return

    providers = env["payment.provider"].search([
        ("code", "=", "cointopay"),
        ("module_id", "=", False),
    ])
    if providers:
        providers.module_id = module
