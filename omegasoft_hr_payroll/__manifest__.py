{
    "name": "Omegasoft C.A Hr Payroll",
    "version": "16.0.0.0.16",
    "category": "Human Resources/Contracts",
    "application": False,
    "author": "Omegasoft C.A.",
    "contributor": [
        "Daniel Ospino - daniel.ospino@omegasoftve.com",
        "Rene Gomez - rene.gomez@omegasoftve.com",
    ],
    "website": "https://github.com/macagua/Closter_l10n_ve",
    "summary": "Hr Payroll",
    "description": """
    Customizations to Hr Payroll.
    """,
    "depends": [
        "hr",
        "hr_payroll",
        "mail",
        "omegasoft_res_currency_payroll_rate",
        "omegasoft_payroll_res_config_settings",
        "omegasoft_contract_utility_liabilities_fields",
        "omegasoft_contract_salary_fields",
        "omegasoft_salary_bonuses_fields",
    ],
    "data": [
        "data/mail_template.xml",
        "views/hr_payroll_send_payslip_by_email.xml",
        "views/res_currency.xml",
        "views/hr_payslip.xml",
        "views/hr_payslip_run.xml",
        "views/hr_payroll_structure.xml",
        "views/hr_payslip_by_employee.xml",
    ],
    "installable": True,
    "auto_install": False,
    "license": "LGPL-3",
}
