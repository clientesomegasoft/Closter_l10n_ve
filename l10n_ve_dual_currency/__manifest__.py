{
    "name": "Omegasoft C.A Moneda operativa",
    "version": "1.0",
    "category": "Accounting/Localizations/Account Charts",
    "author": "Omegasoft C.A",
    "contributor": [
        "Naudy Mendez - naudy.mendez@omegasoftve.com",
    ],
    "website": "https://github.com/macagua/Closter_l10n_ve",
    "summary": "Moneda Operativa",
    "description": """
Moneda Operativa
================
* Registra mas de una tasa por dia
* Selecciona en Asientos contables la tasa con la que deseas trabajar
* Visualiza tus operaciones contables en una moneda secundaria
    """,
    "depends": [
        "stock_account",
        "stock_landed_costs",
        "l10n_ve_config_account",
    ],
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
