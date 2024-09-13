# -*- coding: utf-8 -*-
{
    'name': 'Omegasoft C.A Hr Organizational units',
    'version': '16.0.16',
    'category': 'Human Resources/Employee',
    'application': False,
    'author': 'Omegasoft C.A',
    'contributor': 'Daniel Ospino - daniel.ospino@omegasoftve.com',
    'website': 'https://www.omegasoftve.com/',
    'summary': 'Hr Employee',
    'description': """
    Cost Centers.
    """,
    'depends': [
        'hr',
        'omegasoft_hr_employee',
		'omegasoft_payroll_res_config_settings',
        'hr_appraisal'
        ],
    'data' : [
		    'security/ir.model.access.csv',
            'views/res_config_settings.xml',
            'views/hr_employee.xml',
            'views/hr_organizational_units.xml',
            'views/hr_job.xml',
            'views/hr_department.xml',
        ],
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3'
}
