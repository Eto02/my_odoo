{
    "name": "Midtrans Payment Provider",
    "version": "17.0.1.0.0",
    "category": "Accounting/Payment",
    "summary": "Midtrans Payment Provider for Odoo",
    "depends": ["payment"],
    "data": [
        "security/ir.model.access.csv",
        "views/payment_provider_view.xml",
        "data/payment_provider_data.xml",
    ],
    "assets": {
        "web.assets_frontend": [
            "payment_midtrans/static/src/js/midtrans.js",
        ],
    },
    "installable": True,
}
