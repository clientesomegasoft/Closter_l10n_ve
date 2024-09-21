{
    "name": "Omegasoft C.A Payroll Res Config Settings",
    "version": "16.0.16",
    "category": "Human Resources/Contracts",
    "application": False,
    "author": "Omegasoft C.A",
    "contributor": "Daniel Ospino - daniel.ospino@omegasoftve.com / Rene Gomez - rene.gomez@omegasoftve.com",
    "website": "https://github.com/OCA/l10n-venezuela",
    "summary": "Payroll Res Config Settings",
    "description": """
    Global configurations to the payroll module.
    """,
    "depends": ["hr_payroll"],
    "data": [
        "security/access.xml",
        "security/rules.xml",
        "views/average_wage_lines.xml",
        "views/global_amounts_history.xml",
        "views/custom_payroll_res_config_settings.xml",
        "data/crons.xml",
    ],
    "installable": True,
    "auto_install": False,
    "license": "LGPL-3",
}
