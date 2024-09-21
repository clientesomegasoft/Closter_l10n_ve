{
    "name": "Omegasoft C.A. Account and Sale Statistics",
    "version": "16.0.1",
    "summary": """Customize the standards reports on Account and Sale applications""",
    "description": """
Express the monetary fields/columns that appears in some
analysis reports as amounts in the company's operative
currency, useful for business that work with more than
a single currency in Venezuela.

The reports that are affected by this module are:
    - Invoices Statistics
    - Sales Analysis Report
""",
    "author": "Omegasoft C.A",
    "contributor": [
        "Gabriel Peraza - gabriel.peraza@omegasoftve.com",
    ],
    "website": "https://github.com/OCA/l10n-venezuela",
    "category": "Inventory/Inventory",
    "depends": [
        "account",
        "sale",
        "sale_margin",
        "l10n_ve_config_account",
    ],
    "data": [
        "report/account_invoice_report_view.xml",
        "report/sale_report_view.xml",
    ],
    "license": "LGPL-3",
}
