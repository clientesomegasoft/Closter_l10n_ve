# -*- coding: utf-8 -*-
{
	'name': 'Omegasoft C.A Retenciones de ISLR',
	'version': '1.0',
	'category': 'Accounting/Localizations/Account Charts',
	'author': 'Omegasoft C.A',
	'contributor': [
		'Naudy Mendez - naudy.mendez@omegasoftve.com',
	],
	'website': 'https://www.omegasoftve.com',
	'summary': 'Retenciones de ISLR',
	'description': """
Retenciones de ISLR
===================
Realiza retenciones de impuesto sobre la renta según se especifica en la Ley, aplicable en todo el territorio nacional.
""",
	'depends': [
		'l10n_ve_config_withholding',
	],
	'data': [
		'security/ir.model.access.csv',
		'security/security.xml',
		'data/account.islr.concept.csv',
		'data/account.islr.concept.rate.csv',
		'data/sequence.xml',
		'views/account_islr_concept.xml',
		'views/product_template.xml',
		'views/res_partner_views.xml',
		'views/res_config_settings_views.xml',
		'views/account_withholding_islr.xml',
		'views/account_withholding_islr_xml.xml',
		'views/account_move_views.xml',
		'report/account_withholding_islr_report.xml',
		'data/mail_template_data.xml',
	],
	'application': False,
	'installable': True,
	'auto_install': False,
	'license': 'LGPL-3',
}