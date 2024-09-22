{
    "name": "Omegasoft C.A Estimated Profits",
    "version": "16.0.16",
    "category": "Human Resources/Contracts",
    "application": False,
    "author": "Omegasoft C.A",
    "contributor": [
        "Daniel Ospino - daniel.ospino@omegasoftve.com",
        "Rene Gomez - rene.gomez@omegasoftve.com",
    ],
    "website": "https://github.com/macagua/Closter_l10n_ve",
    "summary": "Hr Estimated Profits",
    "description": """
        Calculation of estimated profits
        """,
    "depends": [
        "hr",
        "omegasoft_payroll_res_config_settings",
        "hr_contract",
        "omegasoft_contract_salary_fields",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/lines_estimated_profit.xml",
        "views/res_config_settings.xml",
        "views/hr_contract.xml",
    ],
    "installable": True,
    "auto_install": False,
    "license": "LGPL-3",
}
