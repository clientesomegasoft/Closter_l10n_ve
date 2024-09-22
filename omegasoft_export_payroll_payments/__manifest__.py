{
    "name": "Omegasoft C.A Export payroll payments",
    "version": "16.0.0.0.16",
    "category": "Human Resources/Payroll",
    "application": False,
    "author": "Omegasoft C.A.",
    "contributor": [
        "Daniel Ospino - daniel.ospino@omegasoftve.com",
        "Rene Gomez - rene.gomez@omegasoftve.com",
    ],
    "website": "https://github.com/macagua/Closter_l10n_ve",
    "summary": "Generation of txt file for mass payroll payments",
    "description": """
        Generation of txt file for mass payroll payments""",
    "depends": ["base", "hr", "hr_payroll", "omegasoft_hr_employee_bank_information"],
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
