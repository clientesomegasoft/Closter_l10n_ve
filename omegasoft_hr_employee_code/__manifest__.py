{
    "name": "Omegasoft Hr Employee Code",
    "summary": """Adds employee file functionality""",
    "author": "Omegasoft C.A., Odoo Community Association (OCA)",
    "contributor": "Luis Alfonzo - luis.alfonzo@omegasoftve.com",
    "website": "https://github.com/OCA/l10n-venezuela",
    "category": "Human Resources/Employee",
    "version": "16.0.0.0.1",
    "depends": ["hr", "hr_payroll", "omegasoft_payroll_res_config_settings"],
    "data": [
        "security/access.xml",
        "security/rules.xml",
        "views/res_config_settings.xml",
        "views/employee_file_code.xml",
        "views/hr_employee.xml",
    ],
    "license": "LGPL-3",
}
