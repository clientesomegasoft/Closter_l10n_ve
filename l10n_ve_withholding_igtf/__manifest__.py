{
    "name": "Omegasoft C.A Retenciones de IGTF",
    "version": "16.0.0.0.1",
    "category": "Accounting/Localizations/Account Charts",
    "author": "Omegasoft C.A.",
    "contributor": [
        "Naudy Mendez - naudy.mendez@omegasoftve.com",
    ],
    "website": "https://github.com/macagua/Closter_l10n_ve",
    "summary": "Retenciones de IGTF",
    "description": """
Retenciones de IGTF
===================
Realiza retenciones de IGTF.
""",
    "depends": ["l10n_ve_config_withholding"],
    "data": [
        "views/res_partner_views.xml",
        "views/res_config_settings_views.xml",
        "views/account_payment.xml",
        "wizard/account_payment_register.xml",
    ],
    "application": False,
    "installable": True,
    "auto_install": False,
    "license": "LGPL-3",
}
