{
    "name": "Omegasoft C.A Employee eventual bonuses",
    "version": "16.0.0.0.16",
    "category": "Human Resources/Employee",
    "application": False,
    "author": "Omegasoft C.A",
    "contributor": [
        "Daniel Ospino - daniel.ospino@omegasoftve.com",
        "Rene Gomez - rene.gomez@omegasoftve.com",
    ],
    "website": "https://github.com/macagua/Closter_l10n_ve",
    "summary": "Allocation of bonuses to employees",
    "description": """
        Allocation of toy and school vouchers, among others.
    """,
    "depends": [
        "base",
        "hr",
        "hr_payroll",
        "mail",
        "portal",
        "omegasoft_hr_employee_family_information",
        "omegasoft_res_currency_payroll_rate",
        "omegasoft_payroll_res_config_settings",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/views.xml",
        "views/employee_bonus.xml",
        "views/employee_bonus_lines.xml",
    ],
    "installable": True,
    "auto_install": False,
    "license": "LGPL-3",
}
