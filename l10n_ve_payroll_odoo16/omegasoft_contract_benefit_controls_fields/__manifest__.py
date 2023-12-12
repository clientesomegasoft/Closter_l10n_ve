# -*- coding: utf-8 -*-
{
    'name': 'Omegasoft C.A Contract Benefit controls Fields',
    'version': '16.0.16',
    'category': 'Human Resources/Contracts',
    'application': False,
    'author': 'Omegasoft C.A',
    'contributor': 'Daniel Ospino - daniel.ospino@omegasoftve.com / Rene Gomez - rene.gomez@omegasoftve.com',
    'website': 'https://www.omegasoftve.com/',
    'summary': 'Benefit controls Fields',
    'description': """
    Adds the basic fields for Benefit controls according to Venezuelan law..
    """,
    'depends': ['hr_contract'],
    'data' : [
        'views/contract_benefit_controls_fields.xml',
        ],
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3'
}
