# -*- coding: utf-8 -*-
{
    'name': 'Omegasoft - Comisiones de venta',
    'version': '16',
    'category': 'Human Resources/Contracts',
    'application': False,
    'author': 'Omegasoft C.A',
    'contributor': 'Daniel Ospino - dospinoomegasoft@omegasoftve.com',
    'website': 'https://www.omegasoftve.com/',
    'summary': 'Sale Comissions',
    'description': """
        Sale Comissions.
    """,
    'depends': [
        'hr_contract',
        'account',
        'sale',
        'product',
        'omegasoft_hr_employee_code',
    ],
    'data' : [
        'security/ir.model.access.csv',
		'data/sequence.xml',
		'views/commission_scale_views.xml',
		'views/hr_department_views.xml',
		'views/hr_contract_views.xml',
		'views/commission_conf_line_views.xml',
		'views/paid_sales_allocation_views.xml',
		'views/account_move_views.xml',
		'views/product_views.xml',
		'views/sale_order_views.xml',
    ],
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3'
}
