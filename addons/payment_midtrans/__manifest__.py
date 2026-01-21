{
    "name": "Midtrans Payment Provider",
    "version": "17.0.1.0.0",
    "category": "Accounting/Payment",
    "summary": "Midtrans Payment Provider Integration for Odoo 17",
    "description": """
        Complete Midtrans payment gateway integration for Odoo 17.
        Supports:
        - Website payment checkout
        - Payment status tracking
        - Webhook notifications
        - Multiple payment methods (Credit Card, Bank Transfer, E-Wallet, etc)
    """,
    "depends": [
        "payment",
        "website_sale",
        "point_of_sale",
        "account",
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/payment_provider_data.xml',                        
        'views/payment_provider_views.xml',       
        'views/payment_midtrans_templates.xml',     
    ],
    'assets': {
        'web.assets_frontend': [
            'payment_midtrans/static/src/js/payment_form.js',
        ],
        'web.assets_backend': [
            'payment_midtrans/static/src/css/payment_dashboard.css',
        ],
        'point_of_sale._pos_assets': [
            'payment_midtrans/static/src/js/payment_form.js',
        ],
    },
    "installable": True,
    "application": False,
    "license": "AGPL-3",
    "author": "Your Company",
    "website": "https://yourcompany.com",
}

