{
    "name": "Omegasoft C.A Hr Employee Bank information",
    "version": "16.0.0.0.16",
    "category": "Human Resources/Contracts",
    "application": False,
    "author": "Omegasoft C.A., Odoo Community Association (OCA)",
    "contributor": [
        "Daniel Ospino - daniel.ospino@omegasoftve.com",
        "Rene Gomez - rene.gomez@omegasoftve.com",
    ],
    "website": "https://github.com/OCA/l10n-venezuela",
    "summary": "Hr Employee Bank information",
    "depends": ["omegasoft_hr_employee_family_information"],
    "data": [
        "security/ir.model.access.csv",
        "views/hr_employee.xml",
        "views/hr_employee_bank_information.xml",
    ],
    "installable": True,
    "auto_install": False,
    "license": "LGPL-3",
}
