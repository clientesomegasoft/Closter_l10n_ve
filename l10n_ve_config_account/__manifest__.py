{
    "name": "Omegasoft C.A Configuración contable",
    "version": "16.0.0.0.1",
    "category": "Accounting/Localizations/Account Charts",
    "author": "Omegasoft C.A.",
    "contributor": [
        "Naudy Mendez - naudy.mendez@omegasoftve.com",
    ],
    "website": "https://github.com/macagua/Closter_l10n_ve",
    "summary": "Configuración Contable",
    "description": """
Configuración Contable
======================
    """,
    "depends": [
        "sale",
        "purchase",
        "l10n_ve_fiscal_identification",
    ],
    "data": [
        "security/ir.model.access.csv",
        "data/menuitems.xml",
        "views/res_config_settings_views.xml",
        "views/account_ut_views.xml",
        "views/sale_order_views.xml",
        "views/purchase_views.xml",
        "views/account_move_views.xml",
    ],
    "application": False,
    "installable": True,
    "auto_install": False,
    "license": "LGPL-3",
}
