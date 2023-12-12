# -*- coding: utf-8 -*-
{
	'name': 'Omegasoft C.A Impuesto al licor',
	'version': '1.0',
	'category': 'Accounting/Localizations/Account Charts',
	'author': 'Omegasoft C.A',
	'contributor': [
		'Naudy Mendez - naudy.mendez@omegasoftve.com',
	],
	'website': 'https://www.omegasoftve.com',
	'summary': 'Impuesto al licor',
	'description': """
Impuesto al Licor
=================
Calcula y declara los impuestos correspondientes a cada concepto de ventas de licor.
""",
	'depends': [
		'l10n_ve_dual_currency',
	],
	'data': [
		'security/ir.model.access.csv',
		'views/account_liquor_tax_views.xml',
		'views/product_template.xml',
		'views/account_liquor_tax_report_views.xml',
	],
	'application': False,
	'installable': True,
	'auto_install': False,
	'license': 'LGPL-3',
}