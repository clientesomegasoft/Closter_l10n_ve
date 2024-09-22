{
    "name": "Omegasoft C.A Hr Employee Disability",
    "version": "16.0.0.0.16",
    "category": "Human Resources/Employee",
    "application": False,
    "author": "Omegasoft C.A.",
    "contributor": [
        "Daniel Ospino - daniel.ospino@omegasoftve.com",
        "Rene Gomez - rene.gomez@omegasoftve.com",
    ],
    "website": "https://github.com/macagua/Closter_l10n_ve",
    "summary": "Hr Employee Disability",
    "description": """
    Employee Disability.
    """,
    "depends": ["hr", "hr_payroll"],
    "data": [
        "data/employee_disability_data.xml",
        "security/ir.model.access.csv",
        "security/rules.xml",
        "views/employee_disability_view.xml",
        "views/views.xml",
        "views/canapdis.xml",
        "reports/canapdis_report.xml",
    ],
    "installable": True,
    "auto_install": False,
    "license": "LGPL-3",
}
