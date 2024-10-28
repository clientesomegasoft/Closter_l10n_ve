{
    "name": "Venezuela - Configuración retenciones",
    "version": "16.0.0.0.1",
    "category": "Accounting/Localizations/Account Charts",
    "author": "Omegasoft C.A., Odoo Community Association (OCA)",
    "contributor": [
        "Naudy Mendez - naudy.mendez@omegasoftve.com",
    ],
    "website": "https://github.com/OCA/l10n-venezuela",
    "summary": "Configuración de Retenciones",
    "depends": [
        "account_debit_note",
        "l10n_ve_dual_currency",
    ],
    "data": [
        "data/withholding_data.xml",
        "views/account_journal_views.xml",
        "views/res_config_settings_views.xml",
        "views/res_partner_views.xml",
    ],
    "application": False,
    "installable": True,
    "auto_install": False,
    "license": "LGPL-3",
}
