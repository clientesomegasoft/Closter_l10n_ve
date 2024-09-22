{
    "name": "Omegasoft C.A Identificación fiscal",
    "version": "16.0.0.0.1",
    "category": "Accounting/Localizations/Account Charts",
    "author": "Omegasoft C.A",
    "contributor": [
        "Naudy Mendez - naudy.mendez@omegasoftve.com",
    ],
    "website": "https://github.com/macagua/Closter_l10n_ve",
    "summary": "Identificación Fiscal",
    "description": """
Identificación Fiscal
=====================
    """,
    "depends": ["base_vat", "sale", "purchase", "account_accountant"],
    "data": [
        "security/ir.model.access.csv",
        "data/person_type_data.xml",
        "views/res_partner_views.xml",
        "views/partner_domain_views.xml",
    ],
    "application": False,
    "installable": True,
    "auto_install": False,
    "license": "LGPL-3",
}
