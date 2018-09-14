# -*- coding: utf-8 -*-

{
    'name': "Cointopay Payment Acquirer",
    'category': 'Accounting',
    'summary': 'Payment Acquirer: Cointopay Implementation',
    'version': '1.0',
    'description': """Cointopay Payment Acquirer""",
    'depends': ['payment'],
    'data': [
        'views/payment_views.xml',
        'views/payment_cointopay_templates.xml',
        'data/payment_acquirer_data.xml',
    ],
    'installable': True
}
