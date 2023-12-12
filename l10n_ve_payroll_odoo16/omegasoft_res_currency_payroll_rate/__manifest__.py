# -*- coding: utf-8 -*-
{
    'name': 'Omegasoft C.A Res Currency Payroll rate',
    'version': '16.0.16',
    'category': 'Currency',
    'application': False,
    'author': 'Omegasoft C.A',
    'contributor': 'Daniel Ospino - daniel.ospino@omegasoftve.com / Rene Gomez - rene.gomez@omegasoftve.com',
    'website': 'https://www.omegasoftve.com/',
    'summary': 'Res currency payroll customization',
    'description': """
        Identifies currency rates as payroll rate or regular rate
    """,
    'depends': ['base', 'l10n_ve_dual_currency'],
    'data' : [
            'views/res_currency_views.xml',
        ],
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3'
}