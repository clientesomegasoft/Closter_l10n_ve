{
    "name": "Omegasoft C.A Contract Salary Fields",
    "version": "16.0.0.0.16",
    "contributor": [
        "Daniel Ospino - daniel.ospino@omegasoftve.com",
        "Rene Gomez - rene.gomez@omegasoftve.com",
    ],
    "application": False,
    "author": "Omegasoft C.A",
    "website": "https://github.com/macagua/Closter_l10n_ve",
    "summary": "Salary Fields",
    "description": """
    Adds the basic fields for salary according to Venezuelan law.
    """,
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
