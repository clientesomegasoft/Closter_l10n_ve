{
    "name": "Omegasoft C.A Contract Allocation",
    "version": "16.0.16",
    "category": "Human Resources/Contracts",
    "application": False,
    "author": "Omegasoft C.A",
    "contributor": "Daniel Ospino - daniel.ospino@omegasoftve.com / Rene Gomez - rene.gomez@omegasoftve.com",
    "website": "https://github.com/OCA/l10n-venezuela",
    "summary": "Allocation of uniforms, personal hygiene and personal equipment to employees",
    "description": """
        Allocation of uniforms, personal hygiene and personal equipment to employees.
    """,
    "depends": [
        "hr",
        "hr_payroll",
        "mail",
        "portal",
        "product",
        "omegasoft_hr_employee",
        "omegasoft_hr_employee_code",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/views.xml",
        "views/contract_allocation.xml",
        "views/contract_allocation_lines.xml",
    ],
    "installable": True,
    "auto_install": False,
    "license": "LGPL-3",
}
