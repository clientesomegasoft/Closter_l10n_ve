{
    "name": "Omegasoft C.A Contract Salary Fields",
    "version": "16.0.0.0.16",
    "contributor": [
        "Daniel Ospino - daniel.ospino@omegasoftve.com",
        "Rene Gomez - rene.gomez@omegasoftve.com",
    ],
    "application": False,
    "author": "Omegasoft C.A., Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/l10n-venezuela",
    "summary": "Salary Fields",
    "depends": [
        "hr_contract",
        "omegasoft_payroll_res_config_settings",
        "omegasoft_hr_employee_code",
    ],
    "data": [
        "views/hr_contract_history.xml",
        "views/contract_salary_fields.xml",
    ],
    "installable": True,
    "auto_install": False,
    "license": "LGPL-3",
}
