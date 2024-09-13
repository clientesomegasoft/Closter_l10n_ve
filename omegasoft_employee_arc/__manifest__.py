# -*- coding: utf-8 -*-
{
	'name': 'Omegasoft C.A Employee ARC report',
	'version': '1.0',
	'description': """
Reporte ARC Empleados
=====================
""",
	'category': 'Human Resources/Contracts',
	'author': 'Omegasoft C.A',
	'website': 'https://www.omegasoftve.com',
	'depends': [
		'hr',
		'hr_payroll',
		'omegasoft_hr_employee',
		'omegasoft_payroll_res_config_settings',
		'omegasoft_hr_employee_code'
	],
	'data': [
		'security/ir.model.access.csv',
		'views/res_config_settings_views.xml',
		'views/res_company.xml',
		'report/employee_arc_report.xml',
		'wizard/employee_arc_report_wizard.xml',
		'data/mail_template_data.xml',
  
	],
	'assets': {
		'web.assets_backend': ['omegasoft_employee_arc/static/src/js/yearpicker.js'],
	},
	'license': 'LGPL-3',
}