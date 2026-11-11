# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    "name": "Payment Provider: Cointopay",
    "version": "1.1",
    "category": "Accounting/Payment Providers",
    "sequence": 350,
    "summary": "Accept cryptocurrency payments with Cointopay.",
    "description": " ",
    "depends": ["payment"],
    "data": [
        "views/payment_cointopay_templates.xml",
        "views/payment_views.xml",
        "data/payment_provider_data.xml",
    ],
    "post_init_hook": "post_init_hook",
    "uninstall_hook": "uninstall_hook",
    "author": "Cointopay",
    "license": "LGPL-3",
    "installable": True,
    "application": False,
}
