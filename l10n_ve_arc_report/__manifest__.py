{
    "name": "Omegasoft C.A ARC Proveedores",
    "version": "16.0.0.0.1",
    "category": "Accounting/Localizations/Account Charts",
    "author": "Omegasoft C.A.",
    "contributor": [
        "Naudy Mendez - naudy.mendez@omegasoftve.com",
    ],
    "website": "https://github.com/macagua/Closter_l10n_ve",
    "summary": "Reporte ARC Proveedores",
    "description": """
Reporte ARC Proveedores
=======================
    """,
    "depends": [
        "l10n_ve_account_reports_dual",
    ],
    "data": [
        "data/arc_report.xml",
        "views/report_templates.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "l10n_ve_arc_report/static/src/js/account_reports.js",
            "l10n_ve_arc_report/static/src/xml/account_report_template.xml",
        ],
    },
    "application": False,
    "installable": True,
    "auto_install": False,
    "license": "LGPL-3",
}
