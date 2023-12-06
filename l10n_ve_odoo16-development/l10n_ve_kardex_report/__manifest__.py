# -*- coding: utf-8 -*-
{
	'name': 'Omegasoft C.A Libro de inventario',
	'version': '1.0',
	'category': 'Inventory/Inventory',
	'author': 'Omegasoft C.A',
	'contributor': [
		'Naudy Mendez - naudy.mendez@omegasoftve.com',
	],
	'website': 'https://www.omegasoftve.com',
	'summary': 'Libro de inventario',
	'description': """
Libro De Inventario
===================
Consulta y controla las entradas de mercancía que se pueden dar por compras a proveedores, ventas clientes, ajustes de mercancía o devoluciones.
""",
	'depends': [
		'l10n_ve_account_reports_dual',
	],
	'data': [
		'data/account_kardex_report.xml',
	],
	'application': False,
	'installable': True,
	'auto_install': False,
	'license': 'LGPL-3',
}