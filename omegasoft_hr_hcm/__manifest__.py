{
    "name": "Omegasoft C.A - HCM",
    "version": "16.0.0.0.1",
    "category": "Human Resources/Employee",
    "author": "Omegasoft C.A., Odoo Community Association (OCA)",
    "contributor": [
        "Gabriel Peraza - gabriel.peraza@omegasoftve.com",
    ],
    "website": "https://github.com/OCA/l10n-venezuela",
    "summary": "Hr Employee",
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
