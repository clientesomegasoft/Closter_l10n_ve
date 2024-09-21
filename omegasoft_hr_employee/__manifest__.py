{
    "name": "Omegasoft C.A Hr Employee",
    "version": "16.0.16",
    "category": "Human Resources/Employee",
    "application": False,
    "author": "Omegasoft C.A",
    "contributor": "Daniel Ospino - daniel.ospino@omegasoftve.com / Rene Gomez - rene.gomez@omegasoftve.com",
    "website": "https://github.com/macagua/Closter_l10n_ve",
    "summary": "Hr Employee",
    "description": """
    Customizations to Hr Employee.
    """,
    "depends": [
        "hr",
        "hr_payroll",
        "omegasoft_contract_salary_fields",
        "l10n_ve_fiscal_identification",
    ],
    "data": [
        "views/hr_employee.xml",
        "views/hr_contract_history_report_views.xml",
    ],
    "installable": True,
    "auto_install": False,
    "license": "LGPL-3",
}
