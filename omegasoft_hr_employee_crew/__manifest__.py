{
    "name": "Omegasoft Hr Employee Crew",
    "summary": """
        create crew master and relate with planning module
        """,
    "author": "Omegasoft C.A., Odoo Community Association (OCA)",
    "contributor": "Luis Alfonzo - luis.alfonzo@omegasoftve.com",
    "website": "https://github.com/OCA/l10n-venezuela",
    "category": "Human Resources",
    "version": "16.0.0.0.1",
    "depends": ["hr", "omegasoft_payroll_planning"],
    "data": [
        "security/ir.model.access.csv",
        "security/rules.xml",
        "views/employee_crew.xml",
        "views/planning_template.xml",
    ],
    "license": "LGPL-3",
}
