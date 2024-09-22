{
    "name": "Omegasoft - Payroll Report Customization",
    "version": "16.0.0.0.1",
    "category": "Human Resources/Contracts",
    "application": False,
    "author": "Omegasoft C.A.",
    "contributor": [
        "Gabriel Peraza - gabriel.peraza@omegasoftve.com",
    ],
    "website": "https://github.com/macagua/Closter_l10n_ve",
    "summary": """
    Adds new salary rule categories that will be included in payslip
    reports""",
    "depends": [
        "hr",
        "hr_payroll",
        "omegasoft_hr_payroll_receipt_payment",
        "omegasoft_payroll_res_config_settings",
    ],
    "data": [
        "views/custom_payroll_res_config_settings.xml",
        "views/hr_salary_rules.xml",
        "views/payroll_receipt_payment.xml",
    ],
    "installable": True,
    "auto_install": False,
    "license": "LGPL-3",
}
