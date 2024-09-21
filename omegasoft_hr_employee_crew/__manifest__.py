{
    "name": "Omegasoft Hr Employee Crew",
    "summary": """
        create crew master and relate with planning module
        """,
    "description": """
    """,
    "author": "Omegasoft C.A",
    "contributor": "Luis Alfonzo - luis.alfonzo@omegasoftve.com",
    "website": "https://github.com/macagua/Closter_l10n_ve",
    "category": "Human Resources",
    "version": "0.1",
    "depends": ["hr", "omegasoft_payroll_planning"],
    "data": [
        "security/ir.model.access.csv",
        "security/rules.xml",
        "views/employee_crew.xml",
        "views/planning_template.xml",
    ],
    "license": "LGPL-3",
}
