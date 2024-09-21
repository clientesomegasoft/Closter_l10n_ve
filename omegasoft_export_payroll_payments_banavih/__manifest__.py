{
    "name": "Omegasoft C.A Export payroll payments BANAVIH",
    "version": "16.0.16",
    "category": "Human Resources/Payroll",
    "application": False,
    "author": "Omegasoft C.A",
    "contributor": "Daniel Ospino - daniel.ospino@omegasoftve.com / Rene Gomez - rene.gomez@omegasoftve.com",
    "website": "https://github.com/macagua/Closter_l10n_ve",
    "summary": "Generation of txt file (BANAVIH) for mass payroll payments.",
    "description": """
        Generation of txt file (BANAVIH) for mass payroll payments.""",
    "depends": [
        "base",
        "omegasoft_export_payroll_payments",
        "omegasoft_contract_parafiscal_contributions_fields",
    ],
    "data": [
        "views/hr_export_payroll_banavih.xml",
        "views/res_config_settings.xml",
    ],
    "installable": True,
    "auto_install": False,
    "license": "LGPL-3",
}
