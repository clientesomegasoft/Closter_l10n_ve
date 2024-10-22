{
    "name": "Omegasoft C.A Reporte de Ingresos Brutos",
    "version": "16.0.0.0.1",
    "category": "Accounting/Localizations/Account Charts",
    "author": "Omegasoft C.A., Odoo Community Association (OCA)",
    "contributor": [
        "Naudy Mendez - naudy.mendez@omegasoftve.com",
    ],
    "website": "https://github.com/OCA/l10n-venezuela",
    "summary": "Declaraciones de Patente de Industria y Comercio",
    "depends": ["l10n_ve_withholding_municipal"],
    "data": [
        "security/ir.model.access.csv",
        "security/security.xml",
        "views/res_town_hall_views.xml",
        "views/res_config_settings_views.xml",
        "views/gross_income_report_views.xml",
    ],
    "application": False,
    "installable": True,
    "auto_install": False,
    "license": "LGPL-3",
}
