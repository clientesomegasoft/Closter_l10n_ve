# -*- coding: utf-8 -*-
{
    'name': 'Omegasoft - Salary Bonuses Fields',
    'version': '15',
    'category': 'Human Resources/Contracts',
    'application': False,
    'author': 'Omegasoft C.A',
    'contributor': 'Ismael Castillo - ismael.castillo@omegasoftve.com',
    'website': 'https://www.omegasoftve.com/',
    'summary': 'Bonuses Fields',
    'description': """
        Adds salary bonuses fields to Venezuela Accountant Localization.
    """,
    'depends': ['omegasoft_contract_bonuses_fields','hr_contract'],
    'data' : [
        'views/hr_contract.xml',
    ],
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3'
}
