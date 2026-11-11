{
    'name': 'Payment Cointopay',
    'summary': 'Integration of Cointopay as a payment provider',
    'description': '''
        Cointopay Payment Provider
        =============================
        This module integrates Cointopay as a payment provider in Odoo.
        It allows customers to pay online using the Cointopay gateway.
    ''',
    'author': 'Wclik Corporation',
    'maintainer': 'Wclik Corporation',
    'company': 'Wclik Corporation',
    'website': 'https://wclik.com',
    'license': 'LGPL-3',
    'category': 'Accounting/Payment Providers',
    'version': '2.3',
    'depends': ['base', 'payment'],
    'data': [
        'views/payment_templates.xml',
        'views/payment_provider_views.xml',
        'data/payment_method_data.xml',
        'data/payment_provider_data.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'post_init_hook': 'post_init_hook',
    'uninstall_hook': 'uninstall_hook',
}
