# -*- coding: utf-8 -*-
{
	'name': 'Omegasoft C.A Libros fiscales',
	'version': '1.0',
	'category': 'Accounting/Localizations/Account Charts',
	'author': 'Omegasoft C.A',
	'contributor': [
		'Naudy Mendez - naudy.mendez@omegasoftve.com',
	],
	'website': 'https://www.omegasoftve.com',
	'summary': 'Libros fiscales Compra / Venta',
	'description': """
Libros fiscales
===============
Visualiza los libros fiscales de compra y venta.
""",
	'depends': [
		'l10n_ve_account_reports_dual',
		'l10n_ve_withholding_iva',
	],
	'data': [
		'data/fiscal_books.xml',
		'views/account_tax_views.xml',
		'views/account_move_views.xml',
	],
	'application': False,
	'installable': True,
	'auto_install': False,
	'license': 'LGPL-3',
}