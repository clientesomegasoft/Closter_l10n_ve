# -*- coding: utf-8 -*-
{
    'name': 'Omegasoft C.A Contract Social benefit liabilities Fields',
    'version': '16.0.16',
    'category': 'Human Resources/Contracts',
    'application': False,
    'author': 'Omegasoft C.A',
    'contributor': 'Daniel Ospino - daniel.ospino@omegasoftve.com / Rene Gomez - rene.gomez@omegasoftve.com',
    'website': 'https://www.omegasoftve.com/',
    'summary': 'Contract Social benefit liabilities Fields',
    'description': """
    Adds the Social Benefit Calculations and basic fields for Social benefit liabilities according to Venezuelan law.
    """,
    'depends': ['hr_contract', 'omegasoft_contract_utility_liabilities_fields', 'omegasoft_contract_employee_seniority', 'omegasoft_contract_benefit_controls_fields', 'omegasoft_payroll_res_config_settings', 'hr_timesheet', 'hr_timesheet_attendance'],
    'data' : [
        'data/social_benefits.xml',
        'views/contract_social_benefit_liabilities_fields.xml',
        'views/employee.xml',
        'views/res_config_settings.xml',
        ],
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3'
}
