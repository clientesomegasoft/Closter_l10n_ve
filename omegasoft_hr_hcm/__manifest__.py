{
    "name": "Omegasoft C.A - HCM",
    "version": "16.0.0.0.1",
    "category": "Human Resources/Employee",
    "author": "Omegasoft C.A",
    "contributor": [
        "Gabriel Peraza - gabriel.peraza@omegasoftve.com",
    ],
    "website": "https://github.com/macagua/Closter_l10n_ve",
    "summary": "Hr Employee",
    "description": """ New configurations for human resources and policy coverage""",
    "depends": ["hr", "omegasoft_hr_employee", "omegasoft_payroll_res_config_settings"],
    "data": [
        "security/ir.model.access.csv",
        "views/hr_employee.xml",
        "views/hr_hcm_coverage_scale.xml",
    ],
    "installable": True,
    "auto_install": False,
    "license": "LGPL-3",
    "application": False,
}
