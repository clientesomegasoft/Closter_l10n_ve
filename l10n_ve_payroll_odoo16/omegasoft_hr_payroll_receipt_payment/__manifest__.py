# -*- coding: utf-8 -*-
{
    'name': 'Omegasoft C.A Hr Payroll Receipt of payment',
    'version': '16.0.16',
    'category': 'Human Resources/Contracts',
    'application': False,
    'author': 'Omegasoft C.A',
    'contributor': 'Daniel Ospino - daniel.ospino@omegasoftve.com / Rene Gomez - rene.gomez@omegasoftve.com',
    'website': 'https://www.omegasoftve.com/',
    'summary': 'Hr Payroll Receipt of payment',
    'description': """
    Customizations to Hr Payroll Receipt of payment.
    """,
    'depends': ['hr_payroll', 'uom', 'omegasoft_payroll_res_config_settings', 'omegasoft_contract_social_benefit_liabilities_fields', 'omegasoft_hr_employee'],
    'data': [
        'security/ir.model.access.csv',
        'data/receipt_payment_names.xml',
        'report/payroll_receipt_payment.xml',
        'views/hr_payroll_structure.xml',
        'views/receipt_payment_name.xml',
        'views/uom_category.xml',
        'views/hr_payslip_other_input.xml',
        'views/custom_payroll_res_config_settings.xml',
    ],
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3'
}
