# -*- coding: utf-8 -*-
{
    'name': 'Omegasoft C.A Contract Bonuses Fields',
    'version': '15.0.1.2',
    'category': 'Human Resources/Contracts',
    'application': False,
    'author': 'Omegasoft C.A',
    'contributor': 'Rene Gomez - rene.gomez@omegasoftve.com',
    'website': 'https://www.omegasoftve.com/',
    'summary': 'Bonuses Fields',
    'description': """
    Adds the basic fields for salary bonuses according to Venezuelan law.
    """,
    'depends': ['hr_contract'],
    'data' : [
        'views/contract_bonuses_fields.xml',
        ],
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3'
}
