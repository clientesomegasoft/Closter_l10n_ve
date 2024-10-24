{
    "name": "Omegasoft C.A Moneda operativa",
    "version": "16.0.0.0.1",
    "category": "Accounting/Localizations/Account Charts",
    "author": "Omegasoft C.A., Odoo Community Association (OCA)",
    "contributor": [
        "Naudy Mendez - naudy.mendez@omegasoftve.com",
    ],
    "website": "https://github.com/OCA/l10n-venezuela",
    "summary": "Moneda Operativa",
    "depends": [
        "stock_account",
        "stock_landed_costs",
        "l10n_ve_config_account",
    ],
    "external_dependencies": {
        "python": [
            "pytz",
        ],
    },
    "data": [
        "views/account_move_views.xml",
        "views/account_payment.xml",
        "views/sale_order_views.xml",
        "views/purchase_views.xml",
        "views/stock_landed_cost_views.xml",
        "views/product_views.xml",
        "views/stock_valuation_layer_views.xml",
        "views/res_currency_views.xml",
        "wizard/account_payment_register.xml",
    ],
    "application": False,
    "installable": True,
    "auto_install": False,
    "license": "LGPL-3",
}
