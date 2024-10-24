{
    "name": "Omegasoft C.A Export payroll payments",
    "version": "16.0.0.0.16",
    "category": "Human Resources/Payroll",
    "application": False,
    "author": "Omegasoft C.A., Odoo Community Association (OCA)",
    "contributor": [
        "Daniel Ospino - daniel.ospino@omegasoftve.com",
        "Rene Gomez - rene.gomez@omegasoftve.com",
    ],
    "website": "https://github.com/OCA/l10n-venezuela",
    "summary": "Generation of txt file for mass payroll payments",
    "depends": [
        "base",
        "hr",
        "hr_payroll",
        "omegasoft_hr_employee_bank_information"
    ],
    'external_dependencies': {
        'python': [
            'pytz',
        ],
    },
    "data": [
        "security/ir.model.access.csv",
        "views/export_bank_payments_views.xml",
        "views/views.xml",
        "data/sequence_data.xml",
    ],
    "installable": True,
    "auto_install": False,
    "license": "LGPL-3",
}
