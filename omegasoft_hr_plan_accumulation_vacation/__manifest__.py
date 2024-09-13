# -*- coding: utf-8 -*-
{
    'name': 'omegasoft hr plan accumulation vacation',
    'version': '16',
    'category': 'Human Resources/vacation',
    'application': False,
    'author': 'Omegasoft C.A',
    'contributor': 'Daniel Ospino - dospinoomegasoft@omegasoftve.com',
    'website': 'https://www.omegasoftve.com/',
    'summary': 'Customization in hr for vacation control',
    'description': """
    New model for hr, for vacation control
    """,
    'depends': ['hr', 
                'hr_payroll',
                'hr_contract',
                'hr_holidays',
                'omegasoft_hr_employee_code',
                'omegasoft_payroll_res_config_settings',
                'omegasoft_hr_employee',
                'omegasoft_contract_employee_seniority',
                ],
    'data' : [
        'security/ir.model.access.csv',
        'data/ir_cron.xml',
        'views/hr_plan_accumulation.xml',
        'views/hr_leave_type_views.xml',
        'views/hr_leave_views.xml',
        'views/hr_employee.xml',
        'views/hr_plan_accumulation_history.xml',
        
        ],
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3'
}
