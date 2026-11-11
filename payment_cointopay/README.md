# Payment Provider: Cointopay

Cointopay cryptocurrency payment provider for Odoo 16 to 20.

## Installation

This module contains Python code, so it must be installed from an Odoo addons
directory. Do **not** use the web UI's *Apps > Import Module* (zip upload)
feature: that feature only loads XML/CSV/SQL data and never imports Python
models, so views referencing the Cointopay fields fail to validate with
`Field "ctp_merchant_id" does not exist in model "payment.provider"`.

1. Copy the `payment_cointopay` directory into an addons path listed in the
   server's `addons_path` option.
2. Restart the Odoo service (or at least update the apps list).
3. Enable developer mode, open **Apps**, click **Update Apps List**, search for
   **Cointopay** and click **Install**.

From the command line:

```bash
./odoo-bin -c odoo.conf -d <database> -i payment_cointopay --stop-after-init
```

## Configuration

Open **Payments > Providers > Cointopay** and fill in:

- **Merchant ID**
- **Security Code**
- **Coin ID**

Then publish the provider and enable it in the desired environment.

## Uninstalling

The provider is linked to its module through `module_id`. This link is required:
without it Odoo considers the provider as "not installed" and refuses to remove
its accounting payment method line, with the error:

```
You can't delete a payment method that is linked to an installed provider.
Linked providers(s): Cointopay
```

Version 1.1 sets `module_id` for fresh installations and repairs existing
providers through `migrations/1.1/post-migrate.py` when the module is updated.
After updating the module, the standard **Uninstall** button works.

If the database is in an already broken state and updating is not possible, use
the separate `cointopay_cleanup` helper module (data-only, so it can be loaded
through **Apps > Import Module** even without Python support). It removes the
Cointopay provider, its accounting payment method line, and the views left
behind by a failed import.

## Odoo Online (SaaS) is not supported

If your database URL ends in `.odoo.com` (for example
`https://mycompany.odoo.com`), it is hosted on **Odoo Online**. Odoo Online does
not allow custom Python modules, and **Apps > Import Module** only loads
XML/CSV/SQL data files, never Python. This module therefore cannot be installed
on Odoo Online; no change to the module can make that work.

Use **Odoo.sh** (push the module folder to the project's GitHub repository) or
an on-premise / VPS Odoo server (copy the folder into `addons_path`).

## Compatibility

- Odoo 16 to 20 use `payment.provider` and are supported by this version.
- Odoo 15 uses the legacy `payment.acquirer` API and requires a separate
  implementation.
