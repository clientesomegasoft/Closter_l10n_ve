# -*- coding: utf-8 -*-
{
	'name': 'Omegasoft C.A Retenciones de IVA',
	'version': '1.0',
	'category': 'Accounting/Localizations/Account Charts',
	'author': 'Omegasoft C.A',
	'contributor': [
		'Naudy Mendez - naudy.mendez@omegasoftve.com',
	],
	'website': 'https://www.omegasoftve.com',
	'summary': 'Retenciones de IVA',
	'description': """
Retenciones de IVA
==================
	""",
	'depends': [
		'l10n_ve_config_withholding',
	],
	'data': [
		'security/ir.model.access.csv',
		'security/security.xml',
		'data/sequence.xml',
		'data/withholding_iva_data.xml',
		'views/res_config_settings_views.xml',
		'views/withholding_iva_rate_views.xml',
		'views/account_withholding_iva.xml',
		'views/account_withholding_iva_txt.xml',
		'views/res_partner_views.xml',
		'views/account_move_views.xml',
		'report/account_withholding_iva_report.xml',
		'data/mail_template_data.xml',
	],
	'application': False,
	'installable': True,
	'auto_install': False,
	'license': 'LGPL-3',
}