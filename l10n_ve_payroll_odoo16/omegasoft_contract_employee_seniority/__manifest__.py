# -*- coding: utf-8 -*-
{
    'name': 'Omegasoft C.A Contract Employee Seniority',
    'version': '16.0.16',
    'category': 'Human Resources/Contracts',
    'application': False,
    'author': 'Omegasoft C.A',
    'contributor': 'Daniel Ospino - daniel.ospino@omegasoftve.com / Rene Gomez - rene.gomez@omegasoftve.com',
    'website': 'https://www.omegasoftve.com/',
    'summary': 'Employee Seniority',
    'description': """
    Adds the basic fields for Employee Seniority.
    """,
    'depends': ['hr_contract'],
    'data' : [
        'data/employee_seniority.xml',
        'views/contract_employee_seniority.xml',
        ],
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3'
}
