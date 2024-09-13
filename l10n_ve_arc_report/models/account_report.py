# -*- coding: utf-8 -*-

import io
import base64
from odoo import models, fields
from odoo.tools.misc import xlsxwriter

class AccountReport(models.Model):
	_inherit = "account.report"
	
	filter_year = fields.Boolean(
		string="Año",
		compute=lambda x: x._compute_report_option_filter('filter_year'), readonly=False, store=True, depends=['root_report_id'],
	)
	filter_partner_id = fields.Boolean(
		string="Proveedor",
		compute=lambda x: x._compute_report_option_filter('filter_partner_id'), readonly=False, store=True, depends=['root_report_id'],
	)

	def _init_options_year(self, options, previous_options=None):
		if self.filter_year:
			options['year'] = previous_options and previous_options.get('year') or fields.Date.today().year

	def _init_options_partner_id(self, options, previous_options=None):
		if self.filter_partner_id:
			options['partner_id'] = previous_options and previous_options.get('partner_id') or False

	def export_to_xlsx(self, options, response=None):
		if self.custom_handler_model_name != 'account.arc.report.handler':
			return super().export_to_xlsx(options, response=response)

		self.ensure_one()
		output = io.BytesIO()
		workbook = xlsxwriter.Workbook(output, {
			'in_memory': True,
			'strings_to_formulas': False,
		})
		
		sheet = workbook.add_worksheet(self.name[:31])
		default_style = workbook.add_format({'font_name': 'Arial', 'font_size': 12, 'border': 1})
		default_border_style = workbook.add_format({'font_name': 'Arial', 'align': 'center', 'border': 2})
		title_style = workbook.add_format({'font_name': 'Arial', 'bold': True, 'border': 1, 'bg_color': '#e7e6e6'})
		bold_style = workbook.add_format({'font_name': 'Arial', 'bold': True, 'align': 'center'})
		border_bold_style = workbook.add_format({'font_name': 'Arial', 'bold': True, 'align': 'center', 'border': 2})
		sign_style = workbook.add_format({'font_name': 'Arial', 'bold': True, 'align': 'center', 'top': 1})
		partner_id = self.env['res.partner'].browse(options['partner_id']['id'])
		company_id = self.env.company.partner_id
		sheet.set_column(1, 6, 20)
		sheet.set_row(1, 20)
		sheet.set_row(4, 20)

		if company_id.image_512:
			sheet.insert_image(1, 1, 'image.png', {'x_scale': 0.2, 'y_scale': 0.2, 'image_data': io.BytesIO(base64.b64decode(company_id.image_512))})
		sheet.merge_range(2, 3, 2, 6, 'RELACION ANUAL DE LA RETENCION DE IMPUESTO SOBRE LA RENTA', bold_style)
		sheet.merge_range(3, 3, 3, 6, 'DESDE: 01/01/{year}  HASTA: 31/12/{year}'.format(year=options['year']), bold_style)
		sheet.merge_range(5, 1, 5, 6, 'DATOS DEL AGENTE DE RETENCION ARC-V', bold_style)
		sheet.merge_range(6, 1, 6, 2, 'Nombre o Razón Social', border_bold_style)
		sheet.merge_range(6, 3, 6, 6, company_id.name, default_border_style)
		sheet.merge_range(7, 1, 7, 2, 'Direccion Fiscal', border_bold_style)
		sheet.merge_range(7, 3, 7, 6, company_id.contact_address.replace('\n', ' '), default_border_style)
		sheet.merge_range(8, 1, 8, 2, 'R.I.F.', border_bold_style)
		sheet.merge_range(8, 3, 8, 6, company_id.vat, default_border_style)
		sheet.merge_range(10, 1, 10, 6, 'DATOS DEL AGENTE BENEFICIARIO', bold_style)
		sheet.merge_range(11, 1, 11, 2, 'Nombre o Razón Social', border_bold_style)
		sheet.merge_range(11, 3, 11, 6, partner_id.name, default_border_style)
		sheet.merge_range(12, 1, 12, 2, 'Direccion Fiscal', border_bold_style)
		sheet.merge_range(12, 3, 12, 6, partner_id.contact_address.replace('\n', ' '), default_border_style)
		sheet.merge_range(13, 1, 13, 2, 'R.I.F.', border_bold_style)
		sheet.merge_range(13, 3, 13, 6, partner_id.vat, default_border_style)
		y_offset = 15
		
		sheet.write(y_offset, 1, 'Mes', title_style)
		x_offset = 2
		for header in options['columns']:
			sheet.write(y_offset, x_offset, header.get('name', ''), title_style)
			x_offset += 1
		y_offset += 1

		for line in self.with_context(no_format=True)._get_lines(options):
			style = line.get('level') == 1 and title_style or default_style
			sheet.write(y_offset, 1, line.get('name', ''), style)
			for x, column in enumerate(line['columns'], 2):
				sheet.write(y_offset, x, column.get('name', ''), style)
			y_offset += 1

		y_offset += 1
		if self.env.company.sign_512:
			sheet.insert_image(y_offset, 5, 'image.png', {'x_scale': 0.4, 'y_scale': 0.4, 'image_data': io.BytesIO(base64.b64decode(self.env.company.sign_512))})
		y_offset += 5
		sheet.merge_range(y_offset, 1, y_offset, 2, 'FIRMA BENEFICIARIO', sign_style)
		sheet.merge_range(y_offset, 5, y_offset, 6, 'FIRMA Y SELLO DEL AGENTE DE RETENCIÓN', sign_style)

		workbook.close()
		output.seek(0)
		generated_file = output.read()
		output.close()
		
		return {
			'file_name': self.get_default_report_filename('xlsx'),
			'file_content': generated_file,
			'file_type': 'xlsx',
		}