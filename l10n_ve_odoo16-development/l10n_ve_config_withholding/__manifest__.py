# -*- coding: utf-8 -*-
{
	'name' : 'Omegasoft C.A Configuración retenciones',
	'version': '1.0',
	'category': 'Accounting/Localizations/Account Charts',
	'author': 'Omegasoft C.A',
	'contributor': [
		'Naudy Mendez - naudy.mendez@omegasoftve.com',
	],
	'website': 'https://www.omegasoftve.com',
	'summary': 'Configuración de Retenciones',
	'description': """
Configuración de Retenciones
============================
""",
	'depends': [
		'account_debit_note',
		'l10n_ve_dual_currency',
	],
	'data': [
		'data/withholding_data.xml',
		'views/account_journal_views.xml',
		'views/res_config_settings_views.xml',
		'views/res_partner_views.xml',
	],
	'application': False,
	'installable': True,
	'auto_install': False,
	'license': 'LGPL-3',
}