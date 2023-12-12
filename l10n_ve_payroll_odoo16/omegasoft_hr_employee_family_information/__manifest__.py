# -*- coding: utf-8 -*-
{
    'name': 'Omegasoft C.A Hr Emplooye Family information',
    'version': '16.0.16',
    'category': 'Human Resources/Contracts',
    'application': False,
    'author': 'Omegasoft C.A',
    'contributor': 'Daniel Ospino - daniel.ospino@omegasoftve.com / Rene Gomez - rene.gomez@omegasoftve.com',
    'website': 'https://www.omegasoftve.com/',
    'summary': 'Hr Emplooye Family information',
    'description': """
    Employee's family information.
    """,
    'depends': ['hr'],
    'data' : [
            'security/ir.model.access.csv',
            'views/hr_employee.xml',
            'views/hr_employee_family_information.xml',
        ],
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3'
}
