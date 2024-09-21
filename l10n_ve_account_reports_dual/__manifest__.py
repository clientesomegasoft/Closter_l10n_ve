{
    "name": "Omegasoft C.A Reportes en moneda operativa",
    "version": "1.0",
    "category": "Accounting/Localizations/Account Charts",
    "author": "Omegasoft C.A",
    "contributor": [
        "Carlos Carvajal - carlos.carvajal@omegasoftve.com"
        "Naudy Mendez - naudy.mendez@omegasoftve.com",
    ],
    "website": "https://github.com/OCA/l10n-venezuela",
    "summary": "Reportes en moneda operativa",
    "description": """
Reportes en moneda operativa
============================
Permite visualizar los informes contables en la moneda de referencia
""",
    "depends": ["account_followup", "product_margin", "l10n_ve_dual_currency"],
    "data": [
        "views/account_report.xml",
        "views/product_product_views.xml",
        "views/account_followup_views.xml",
    ],
    "application": False,
    "installable": True,
    "auto_install": False,
    "license": "LGPL-3",
}
