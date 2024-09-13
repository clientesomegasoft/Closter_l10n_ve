# -*- coding: utf-8 -*-
{
    'name': "Omegasoft C.A HR Report Letters",
    'version': '16.0.16',
    'category': 'Human Resources',
    'author': "Omegasoft C.A",
    'contributor': 'Carlos Carvajal carlos.carvajal@omegasoftve.com',
    'website': 'https://www.omegasoftve.com/',
    'summary': 'Generation of Report Letters',
    'description': """
        Generation of Report Letters""",
    'depends': ['omegasoft_hr_employee', 'omegasoft_export_payroll_payments'],
    'data': [
        'security/ir.model.access.csv',
        'wizard/report_letters_wizard.xml',
        'report/report_templates.xml'
    ],
    'license': 'LGPL-3',
}
