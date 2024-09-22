{
    "name": "Omegasoft C.A Hr Employee Family information",
    "version": "16.0.0.0.16",
    "category": "Human Resources/Contracts",
    "application": False,
    "author": "Omegasoft C.A.",
    "contributor": [
        "Daniel Ospino - daniel.ospino@omegasoftve.com",
        "Rene Gomez - rene.gomez@omegasoftve.com",
    ],
    "website": "https://github.com/macagua/Closter_l10n_ve",
    "summary": "Hr Employee Family information",
    "description": """
    Employee's family information.
    """,
    "depends": ["hr"],
    "data": [
        "security/ir.model.access.csv",
        "views/hr_employee.xml",
        "views/hr_employee_family_information.xml",
    ],
    "installable": True,
    "auto_install": False,
    "license": "LGPL-3",
}
