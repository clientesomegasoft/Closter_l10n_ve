# -*- coding: utf-8 -*-
{
    'name': 'Omegasoft C.A Hr Emplooye Advances, loans and discounts',
    'version': '16.0.16',
    'category': 'Human Resources/Contracts',
    'application': False,
    'author': 'Omegasoft C.A',
    'contributor': 'Daniel Ospino - daniel.ospino@omegasoftve.com / Rene Gomez - rene.gomez@omegasoftve.com',
    'website': 'https://www.omegasoftve.com/',
    'summary': 'Hr Emplooye Advances, loans and discounts',
    'description': """
    Employee's Advances, loans and discounts.
    """,
    'depends': ['hr','hr_payroll', 'mail','portal', 'hr_contract', 'omegasoft_hr_employee', 'omegasoft_hr_employee_bank_information', 'omegasoft_hr_payroll', 'omegasoft_hr_employee_code'],
    'data' : [
            'security/ir.model.access.csv',
            'views/views.xml',
            'views/hr_employee_advances_loans_discounts.xml',
            'views/hr_employee_advances_loans_discounts_lines.xml',
            'views/hr_contract.xml',
            'views/hr_payroll_structure.xml',
        ],
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3'
}
