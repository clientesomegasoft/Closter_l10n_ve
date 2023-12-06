# -*- coding: utf-8 -*-
{
	'name' : 'Omegasoft C.A Identificación fiscal',
	'version': '1.0',
	'category': 'Accounting/Localizations/Account Charts',
	'author': 'Omegasoft C.A',
	'contributor': [
		'Naudy Mendez - naudy.mendez@omegasoftve.com',
	],
	'website': 'https://www.omegasoftve.com',
	'summary': 'Identificación Fiscal',
	'description': """
Identificación Fiscal
=====================
	""",
	'depends': [
		'base_vat',
		'sale',
		'purchase',
		'account_accountant'
	],
	'data': [
		'security/ir.model.access.csv',
		'data/person_type_data.xml',
		'views/res_partner_views.xml',
		'views/partner_domain_views.xml',
	],
	'application': False,
	'installable': True,
	'auto_install': False,
	'license': 'LGPL-3',
}