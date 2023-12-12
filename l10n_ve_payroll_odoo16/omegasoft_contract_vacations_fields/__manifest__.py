# -*- coding: utf-8 -*-
{
    'name': 'Omegasoft C.A Contract Vacations Fields',
    'version': '16.0.16',
    'category': 'Human Resources/Contracts',
    'application': False,
    'author': 'Omegasoft C.A',
    'contributor': 'Daniel Ospino - daniel.ospino@omegasoftve.com / Rene Gomez - rene.gomez@omegasoftve.com',
    'website': 'https://www.omegasoftve.com/',
    'summary': 'Contract Vacations Fields',
    'description': """
    Adds the basic fields for Vacations according to Venezuelan law.
    """,
    'depends': ['hr_contract', 'omegasoft_contract_utility_liabilities_fields'],
    'data' : [
        'views/contract_vacations_fields.xml',
        ],
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3'
}
