# -*- coding: utf-8 -*-
{
	'name': 'Omegasoft C.A Secuencias de factura de cliente',
	'version': '1.0',
	'category': 'Accounting/Localizations/Account Charts',
	'author': 'Omegasoft C.A',
	'contributor': [
		'Naudy Mendez - naudy.mendez@omegasoftve.com',
	],
	'website': 'https://www.omegasoftve.com',
	'summary': 'Secuencias de factura de cliente',
	'description': """
Secuencias de factura de cliente
================================
	""",
	'depends': [
		'l10n_ve_fiscal_book_report',
	],
	'data': [
		'security/ir.model.access.csv',
		'security/security.xml',
		'views/account_journal_views.xml',
		'views/account_sale_sequence_views.xml',
		'views/account_move_views.xml',
	],
	'application': False,
	'installable': True,
	'auto_install': False,
	'license': 'LGPL-3',
}