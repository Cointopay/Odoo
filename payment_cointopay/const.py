
# Mapping of transaction states to Cointopay payment statuses.
PAYMENT_STATUS_MAPPING = {
    'done': (
        'paid',
        'vtoken-claimed',
    ),
    'pending': (
        'waiting',
        'awaiting-fiat',
        'underpaid',
        'vtoken-open',
    ),
    'failed': (
        'failed',
        'expired',
    ),
}


SUPPORTED_CURRENCIES = [
    'BRL',
    'EUR',
    'USD',
    'CAD',
    'GBP',
    'AUD',
    'CNY',
    'JPY',
    'CHF',
    'KRW',
    'ISK',
    'SGD',
    'HKD',
    'NZD',
    'DKK',
    'SEK',
    'PLN',
    'THB',
    'TWD',
    'AED',
    'PKR',
    'MXN',
    'ZAR',
    'ILS',
    'INR',
    'PHP',
    'CZK',
    'BGN',
    'TRY',
    'HUF',
    'RON',
    'QAR',
]

# The codes of the payment methods to activate when Cointopay is activated.
DEFAULT_PAYMENT_METHOD_CODES = {
    # Primary payment methods.
    'cointopay',
    'bank_account',
}
