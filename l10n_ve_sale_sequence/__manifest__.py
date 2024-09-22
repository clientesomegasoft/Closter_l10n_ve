{
    "name": "Omegasoft C.A Secuencias de factura de cliente",
    "version": "16.0.0.0.1",
    "category": "Accounting/Localizations/Account Charts",
    "author": "Omegasoft C.A.",
    "contributor": [
        "Naudy Mendez - naudy.mendez@omegasoftve.com",
    ],
    "website": "https://github.com/macagua/Closter_l10n_ve",
    "summary": "Secuencias de factura de cliente",
    "depends": [
        "l10n_ve_fiscal_book_report",
    ],
    "data": [
        "security/ir.model.access.csv",
        "security/security.xml",
        "views/account_journal_views.xml",
        "views/account_sale_sequence_views.xml",
        "views/account_move_views.xml",
    ],
    "application": False,
    "installable": True,
    "auto_install": False,
    "license": "LGPL-3",
}
