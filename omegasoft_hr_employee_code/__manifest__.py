{
    "name": "Omegasoft Hr Employee Code",
    "summary": """adds employee file functionality""",
    "description": """
        Adds the employee tab field to various views of the employee module and adds employee search by file
    """,
    "author": "Omegasoft C.A",
    "contributor": "Luis Alfonzo - luis.alfonzo@omegasoftve.com",
    "website": "https://github.com/macagua/Closter_l10n_ve",
    "category": "Human Resources/Employee",
    "version": "0.1",
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
